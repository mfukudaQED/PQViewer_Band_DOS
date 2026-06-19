# PQViewer Remote Open fixed-token setup

Run this once after `git clone` on Windows:

```bat
tools\setup_windows_path.bat
```

This generates:

```text
tools\pqv_token.txt
```

and sets the user environment variables:

```text
PQVIEWER_ROOT
PQVIEWER_TOOLS
PQV_TOKEN
```

It also adds `tools` to the user PATH.

On the remote machine, run:

```bash
bash tools/setup_remote_path.sh --token TOKEN_PRINTED_BY_WINDOWS_SETUP
source ~/.bashrc
```

If the token file is copied to the remote repository as `tools/pqv_token.txt`, you can simply run:

```bash
bash tools/setup_remote_path.sh
source ~/.bashrc
```

After setup:

```bash
pqv-open --open-target main
pqv-open --target main sample.BAND sample.DOS.Tetrahedron
```
