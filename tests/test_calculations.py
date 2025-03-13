import pathlib

import pytest
import subprocess
from aiida.common import folders

from aiida_icon import calculations

@pytest.mark.icon_installed
def test_calc(aiida_computer_local, aiida_code_installed, tmp_path):
    import aiida
    import functools
    result = subprocess.run(["which", "icon"], capture_output=True)
    if result.returncode:
        raise RuntimeError("Could not fine icon executable for tests.")
    filepath_executable = result.stdout.decode().strip()
    code = aiida_code_installed(default_calc_job_plugin="icon.icon", computer=aiida_computer_local(), filepath_executable=filepath_executable)
    datapath = pathlib.Path(__file__).parent.absolute() / "data" / "simple_icon_run"
    builder = code.get_builder()
    make_remote = functools.partial(aiida.orm.RemoteData, computer=code.computer)
    builder.master_namelist = aiida.orm.SinglefileData(datapath / "inputs" / "icon_master.namelist")
    builder.model_namelist = aiida.orm.SinglefileData(datapath / "inputs" / "model.namelist")
    builder.dynamics_grid_file = make_remote(remote_path=str(datapath.absolute() / "inputs" / "icon_grid_simple.nc"))
    builder.ecrad_data = make_remote(remote_path=str(datapath.absolute() / "inputs" / "ecrad_data"))
    builder.rrtmg_sw = make_remote(remote_path=str(datapath.absolute() / "inputs" / "rrtmg_sw.nc"))
    builder.cloud_opt_props = make_remote(remote_path=str(datapath.absolute() / "inputs" / "ECHAM6_CldOptProps.nc"))
    builder.dmin_wetgrowth_lookup = make_remote(
        remote_path=str(datapath.absolute() / "inputs" / "dmin_wetgrowth_lookup.nc")
    )
    result = aiida.run(builder)

    #assert result.works

    #prepare_path = tmp_path / "test_prepare_simple"
    #prepare_path.mkdir()
    #sandbox_folder = folders.SandboxFolder(prepare_path.absolute())
    #calcinfo = icon_calc.presubmit(sandbox_folder)

    #outputs_2d = sandbox_folder.get_subfolder("simple_icon_run_atm_2d", create=False)
    #outputs_3d = sandbox_folder.get_subfolder("simple_icon_run_atm_3d_pl", create=False)
    #remote_link_names = [triplet[2] for triplet in calcinfo.remote_symlink_list]
    #local_copy_names = [triplet[2] for triplet in calcinfo.local_copy_list]

    #assert outputs_2d.exists()
    #assert outputs_3d.exists()
    #assert "simple_icon_run.namelist" in local_copy_names
    #assert "icon_grid_simple.nc" in remote_link_names
    #assert "./ecrad_data" in remote_link_names


def test_prepare_for_calc(icon_calc, tmp_path):
    prepare_path = tmp_path / "test_prepare_simple"
    prepare_path.mkdir()
    sandbox_folder = folders.SandboxFolder(prepare_path.absolute())
    calcinfo = icon_calc.presubmit(sandbox_folder)

    outputs_2d = sandbox_folder.get_subfolder("simple_icon_run_atm_2d", create=False)
    outputs_3d = sandbox_folder.get_subfolder("simple_icon_run_atm_3d_pl", create=False)
    remote_link_names = [triplet[2] for triplet in calcinfo.remote_symlink_list]
    local_copy_names = [triplet[2] for triplet in calcinfo.local_copy_list]

    assert outputs_2d.exists()
    assert outputs_3d.exists()
    assert "simple_icon_run.namelist" in local_copy_names
    assert "icon_grid_simple.nc" in remote_link_names
    assert "./ecrad_data" in remote_link_names


def test_parser_simple(parser_case, icon_result):
    """Parsed output links and exit code should match expectations."""
    parser = calculations.IconParser(icon_result)
    exit_code = parser.parse()

    assert exit_code.status == parser_case.exit_code

    assert all(link in parser.outputs for link in parser_case.required_output_links)
    assert all(link not in parser.outputs for link in parser_case.disallowed_output_links)
    assert parser.outputs.finish_status.value == parser_case.finish_status_value


@pytest.mark.parametrize("case_name", ["restarts_present"])
def test_additional_restart_parsing(case_name, parser_case, icon_result):
    """Check the contents of restarts related parsing outputs."""
    parser = calculations.IconParser(icon_result)
    parser.parse()
    assert pathlib.Path(parser.outputs.latest_restart_file.get_remote_path()).name == "multifile_restart_atm.mfr"
    assert (
        pathlib.Path(parser.outputs.all_restart_files["restart_20000101T030000Z"].get_remote_path()).name
        == "multifile_restart_atm_20000101T030000Z.mfr"
    )
