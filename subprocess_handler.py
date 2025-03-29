import subprocess
import os
import traceback

def _check_if_file_exists(input_path):
    """
    Checks if a file exists and returns the absolute path.
    """
    if not os.path.exists(input_path):
        print(f"⚠️ WARNING: Input file not found at: {input_path}")
        # List directory contents to see what's there
        directory = os.path.dirname(input_path) or '.'
        print(f"Contents of directory {directory}:")
        for file in os.listdir(directory):
            print(f"  - {file}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    else:
        print(f"✅ Input file exists: {input_path}")
        print(f"File size: {os.path.getsize(input_path)} bytes")
        return True


def _run_subprocess_command(tool_name, command, abs_output_path, verbose=True):
    """
    Runs a subprocess command and returns the output.
    """
    # Run the command using subprocess.run
    try:
        subprocess.run(command, capture_output=True, text=True, timeout=300, check=True, verbose=True)
        
        # Check if the output file was created
        if os.path.exists(abs_output_path):
            print(f"Successfully created output file: {abs_output_path}")
            print(f"File size: {os.path.getsize(abs_output_path)} bytes")
            return True
        else:
            print("Error: Output file was not created despite successful command execution")
            return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        traceback.print_exc()
        raise e


def protonate_structure_with_pdb2pqr(input_path, output_path, pH=7.4, verbose=True):
    """
    Adds hydrogens to a protein structure at a specified pH using PDB2PQR.
    """
    # Print current working directory
    print(f"Current working directory: {os.getcwd()}")
    
    # Convert to absolute paths
    abs_input_path = os.path.abspath(input_path)
    abs_output_path = os.path.abspath(output_path)
    
    _check_if_file_exists(abs_input_path)
      
    # Construct the command as a list (recommended to avoid shell injection)
    command = [
        "pdb2pqr30",
        "--ff", "AMBER",
        "--keep-chain",
        "--titration-state-method", "propka",
        "--with-ph", str(pH),
        abs_input_path,
        abs_output_path
    ]
    print("Using absolute input path:", abs_input_path)
    print("Using absolute output path:", abs_output_path)
    print("Full command:", " ".join(command))

    _run_subprocess_command(command, abs_output_path, verbose=True)
    
def optimize_structure_with_molprobity(input_path, output_path, verbose=True):
    """
    Optimizes the structure by adding hydrogens with Asn/Gln/His flips where needed using MolProbity's reduce tool.
    
    Args:
        input_path: Path to the input protein file (PDB format)
        output_path: Path for the output PDB file with hydrogens
    """
    # Convert to absolute paths
    abs_input_path = os.path.abspath(input_path)
    abs_output_path = os.path.abspath(output_path)
    
    _check_if_file_exists(abs_input_path)
    
    command = [
        "reduce",
        "-FLIP",
        abs_input_path,
        ">",
        abs_output_path
    ]
    
    print(f"Attempting to run: reduce -FLIP {abs_input_path} > {abs_output_path}")
    
    # The reduce command needs shell=True to handle redirection
    try:
        # First try the reduce command directly with shell redirection
        shell_command = f"reduce -FLIP {abs_input_path} > {abs_output_path}"
        print(f"Running shell command: {shell_command}")
        subprocess.run(shell_command, shell=True, check=True, stderr=subprocess.PIPE)
        
        # Check if the output file was created and has content
        if os.path.exists(abs_output_path) and os.path.getsize(abs_output_path) > 0:
            print(f"Successfully created output file: {abs_output_path}")
            print(f"File size: {os.path.getsize(abs_output_path)} bytes")
            return True
        else:
            # If the redirection didn't work, try capturing output and writing to file
            print("Output file not created or empty. Trying alternative method...")
            alt_command = ["reduce", "-FLIP", abs_input_path]
            result = subprocess.run(alt_command, capture_output=True, text=True, check=False)
            
            # Check if command succeeded
            if result.returncode != 0:
                print(f"reduce command failed with return code {result.returncode}")
                print(f"STDERR: {result.stderr}")
                
                # Try one more alternative - maybe the command is available but needs different options
                print("Trying with basic reduce options (no -FLIP)...")
                basic_command = ["reduce", abs_input_path]
                basic_result = subprocess.run(basic_command, capture_output=True, text=True, check=False)
                
                if basic_result.returncode != 0:
                    print(f"Basic reduce command also failed with return code {basic_result.returncode}")
                    print(f"STDERR: {basic_result.stderr}")
                    raise RuntimeError(f"Failed to run reduce command: {result.stderr}")
                else:
                    # Write the successful output to file
                    with open(abs_output_path, 'w') as f:
                        f.write(basic_result.stdout)
                    print(f"Successfully created output file using basic reduce command: {abs_output_path}")
                    return True
            else:
                # Write the stdout to the output file
                with open(abs_output_path, 'w') as f:
                    f.write(result.stdout)
                print(f"Successfully created output file using alternative method: {abs_output_path}")
                return True
    except Exception as e:
        print(f"Error running reduce command: {str(e)}")
        traceback.print_exc()
        
        # Fallback to OpenBabel if reduce fails
        print("Falling back to OpenBabel for hydrogen addition...")
        try:
            obabel_command = [
                "obabel",
                "-ipdb", abs_input_path,
                "-opdb",
                "-O", abs_output_path,
                "-h"  # Add hydrogens
            ]
            print(f"Running fallback command: {' '.join(obabel_command)}")
            subprocess.run(obabel_command, check=True, capture_output=True)
            
            if os.path.exists(abs_output_path) and os.path.getsize(abs_output_path) > 0:
                print(f"Successfully created output file using OpenBabel: {abs_output_path}")
                return True
            else:
                raise RuntimeError("Failed to create output file with OpenBabel")
        except Exception as obabel_error:
            print(f"OpenBabel fallback also failed: {str(obabel_error)}")
            raise RuntimeError(f"All structure optimization methods failed: {str(e)}, then {str(obabel_error)}")


def convert_file_with_openbabel(input_path, output_path, verbose=True):
    """
    Converts a file to a PDB file using Open Babel.
    """
    print(f"Converting file: {input_path} -> {output_path}")

    # Convert to absolute paths
    abs_input_path = os.path.abspath(input_path)
    abs_output_path = os.path.abspath(output_path)
    
    _check_if_file_exists(abs_input_path)
        
    # Determine file formats from extensions
    input_ext = os.path.splitext(input_path)[1].lower().lstrip('.')
    output_ext = os.path.splitext(output_path)[1].lower().lstrip('.')
    
    # Map file extensions to OpenBabel format codes
    format_map = {
        'pdb': 'pdb',
        'pqr': 'pqr',
        'mol': 'mol',
        'mol2': 'mol2',
        'sdf': 'sdf',
        'xyz': 'xyz',
        'pdbqt': 'pdbqt',
        'mmcif': 'cif',
        'cif': 'cif'
        # Add other formats as needed
    }
    
    # Get format codes
    input_format = format_map.get(input_ext)
    output_format = format_map.get(output_ext)
    
    # Check if we can handle these formats
    if not input_format:
        print(f"Warning: Unrecognized input format '{input_ext}'. Using extension as format code.")
        input_format = input_ext
    
    if not output_format:
        print(f"Warning: Unrecognized output format '{output_ext}'. Using extension as format code.")
        output_format = output_ext
    
    # Construct OpenBabel command
    command = [
        "obabel",
        f"-i{input_format}", abs_input_path,
        f"-o{output_format}",
        "-O", abs_output_path
    ]
    
    print(f"Running command: {' '.join(command)}")

    _run_subprocess_command(tool_name="OpenBabel", command=command, abs_output_path=abs_output_path, verbose=True)


def convert_to_pdbqt_with_mgltools(input_path, output_path, verbose=True):
    """
    Converts a protein structure file to PDBQT format using MGLTools.
    
    Args:
        input_path: Path to the input protein file (PDB format)
        output_path: Path for the output PDBQT file
    """
    # Convert to absolute paths
    abs_input_path = os.path.abspath(input_path)
    abs_output_path = os.path.abspath(output_path)
    
    _check_if_file_exists(abs_input_path)
    
    # Define paths to MGLTools executables
    mgltools_path = os.path.join('/Users/ingrid/PycharmProjects/jupyternotebook/mgltools_1.5.7_MacOS-X')
    pythonsh = os.path.join(mgltools_path, 'bin', 'pythonsh')
    prepare_receptor_script = os.path.join(mgltools_path, 'MGLToolsPckgs', 'AutoDockTools', 'Utilities24', 'prepare_receptor4.py')
    
    # Ensure the MGLTools paths exist
    _check_if_file_exists(pythonsh)
    _check_if_file_exists(prepare_receptor_script)
    
    command = [
        pythonsh,
        prepare_receptor_script,
        "-r", abs_input_path,
        "-o", abs_output_path,
        "-A", "hydrogens"  # Add hydrogens
    ]
    
    print(f"Running command: {' '.join(command)}")
    
    _run_subprocess_command(tool_name="MGLTools", command=command, abs_output_path=abs_output_path, verbose=True)


def convert_receptor_to_pdbqt_with_openbabel(input_path, output_path, verbose=True):
    """
    Converts a protein structure file to PDBQT format using OpenBabel.
    
    Args:
        input_path: Path to the input protein file (PDB format)
        output_path: Path for the output PDBQT file
    """
    # Convert to absolute paths
    abs_input_path = os.path.abspath(input_path)
    abs_output_path = os.path.abspath(output_path)
    
    _check_if_file_exists(abs_input_path)
    
    # Construct OpenBabel command
    command = [
        "obabel",
        "-ipdb", abs_input_path,
        "-opdbqt",
        "-O", abs_output_path,
        "-xr"  # Add hydrogens, compute Gasteiger charges, and merge non-polar hydrogens
    ]
    
    print(f"Running command: {' '.join(command)}")
    
    _run_subprocess_command(tool_name="OpenBabel", command=command, abs_output_path=abs_output_path, verbose=True)


def convert_ligand_to_pdbqt_with_openbabel(input_path, output_path, generate_3d=False, verbose=True):
    """
    Converts a ligand file to PDBQT format using OpenBabel.
    
    Args:
        input_path: Path to the input ligand file
        output_path: Path for the output PDBQT file
        generate_3d: Whether to generate 3D coordinates for the ligand
    """
    # Convert to absolute paths
    abs_input_path = os.path.abspath(input_path)
    abs_output_path = os.path.abspath(output_path)
    
    _check_if_file_exists(abs_input_path)
    
    # Determine file format from extension
    input_ext = os.path.splitext(abs_input_path)[1].lower().lstrip('.')
    
    # Map file extensions to OpenBabel format codes
    format_map = {
        'pdb': 'pdb',
        'mol': 'mol',
        'mol2': 'mol2',
        'sdf': 'sdf',
        'smi': 'smi',
        'smiles': 'smi'
        # Add other formats as needed
    }
    
    # Get format code
    input_format = format_map.get(input_ext)
    
    # Check if we can handle this format
    if not input_format:
        print(f"Warning: Unrecognized input format '{input_ext}'. Using extension as format code.")
        input_format = input_ext
    
    # Construct OpenBabel command
    command = [
        "obabel",
        f"-i{input_format}", abs_input_path,
        "-opdbqt",
        "-O", abs_output_path,
        "-xh"  # Add hydrogens, compute Gasteiger charges
    ]
    
    # Add 3D generation if requested
    if generate_3d:
        command.extend(["--gen3d"])
    
    print(f"Running command: {' '.join(command)}")
    
    _run_subprocess_command(tool_name="OpenBabel", command=command, abs_output_path=abs_output_path, verbose=True)


def convert_ligand_to_pdbqt_with_mgltools(input_path, output_path):
    """
    Converts a ligand file to PDBQT format using MGLTools.
    
    Args:
        input_path: Path to the input ligand file (PDB format)
        output_path: Path for the output PDBQT file
    """
    # Convert to absolute paths
    abs_input_path = os.path.abspath(input_path)
    abs_output_path = os.path.abspath(output_path)
    
    _check_if_file_exists(abs_input_path)
    
    # Define paths to MGLTools executables
    mgltools_path = os.path.join('/Users/ingrid/PycharmProjects/jupyternotebook/mgltools_1.5.7_MacOS-X')
    pythonsh = os.path.join(mgltools_path, 'bin', 'pythonsh')
    prepare_ligand_script = os.path.join(mgltools_path, 'MGLToolsPckgs', 'AutoDockTools', 'Utilities24', 'prepare_ligand4.py')
    
    # Ensure the MGLTools paths exist
    _check_if_file_exists(pythonsh)
    _check_if_file_exists(prepare_ligand_script)
    
    command = [
        pythonsh,
        prepare_ligand_script,
        "-l", abs_input_path,
        "-o", abs_output_path,
        "-A", "hydrogens"  # Add hydrogens
    ]
    
    print(f"Running command: {' '.join(command)}")
    
    _run_subprocess_command(tool_name="MGLTools", command=command, abs_output_path=abs_output_path, verbose=True) 