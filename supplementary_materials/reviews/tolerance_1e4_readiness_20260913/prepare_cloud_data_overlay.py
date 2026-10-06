"""Create a new data overlay; existing cloud input directories are read-only."""
from pathlib import Path
import argparse
import shutil


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-data',required=True,type=Path)
    p.add_argument('--output-data',required=True,type=Path)
    p.add_argument('--overrides',required=True,type=Path)
    a=p.parse_args()
    base=a.base_data.resolve(strict=True);out=a.output_data.resolve()
    overrides=a.overrides.resolve(strict=True)
    if base==out or base in out.parents or out in base.parents:
        raise ValueError('Overlay must be separate from the original data tree')
    if not (base/'hydro').is_dir() or not (overrides/'hydro').is_dir():
        raise ValueError('Missing base or corrected hydro data')
    out.mkdir(parents=True,exist_ok=False)
    for child in base.iterdir():
        if child.name!='hydro':
            (out/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
    (out/'hydro').mkdir()
    for child in (base/'hydro').iterdir():
        (out/'hydro'/child.name).symlink_to(child.resolve(),target_is_directory=child.is_dir())
    for child in (overrides/'hydro').iterdir():
        target=out/'hydro'/child.name
        if target.exists() or target.is_symlink():raise FileExistsError(target)
        if child.is_dir():shutil.copytree(child,target)
        else:shutil.copy2(child,target)
    print(out)


if __name__=='__main__':main()
