# Offline Linux Bundle

This project supports an offline Linux delivery mode.

## What you get

The build process creates a self-contained Linux bundle:

- `dist/trada-studio-linux-x86_64.tar.gz`

This bundle is intended to be copied to a Linux computer that has no internet access.

## Important limitation

The Linux executable must be built from a Linux environment.

You cannot reliably generate a native Linux executable from macOS without a Linux build environment. In this repository you have two supported ways to build it:

1. Run `bash scripts/build_linux_bundle.sh` on a Linux machine with internet access.
2. Push the project to GitHub and use the workflow `.github/workflows/build-linux-bundle.yml`.

## How to use it on the offline Linux machine

1. Copy `trada-studio-linux-x86_64.tar.gz` to the target machine, for example with a USB drive.
2. Extract it:

```bash
tar -xzf trada-studio-linux-x86_64.tar.gz
```

3. Start the application:

```bash
./trada-studio/trada-studio
```

4. The app opens locally in the browser and does not need internet access.

## Notes

- The bundle includes the compiled frontend and the bundled Python runtime produced by PyInstaller.
- Study data remains local in the bundled `storage/` directory.
- If you want to preserve studies between executions, keep the extracted `trada-studio/` folder and reuse it.
