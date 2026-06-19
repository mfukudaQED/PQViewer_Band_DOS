# PQViewer Remote Open User Setup Guide

This guide explains how to send files on a remote server to **PQViewer** running in a browser on your local PC and display them there.

You can perform the following operations.

```bash
# Open a remote file in a new Viewer
pqv-open band.dat

# Open multiple files together in a single Viewer
pqv-open --same-view sample.BAND sample.DOS.Tetrahedron

# Open a named Viewer and add files to it later
pqv-open --open-target main
pqv-open --target main new_band.dat
```

---

## 1. Distributed File Structure

The GitHub repository is assumed to have the following structure.

```text
PQViewer_Band_DOS/
├── index.html
└── tools/
    ├── pqv-open
    ├── pqv_agent.py
    ├── pqv_agent.bat
    ├── setup_windows_path.bat
    ├── setup_remote_path.sh
    └── show_pqv_token.bat
```

`tools/pqv_token.txt` is secret information that is automatically generated during setup. Do not commit it to GitHub.

It is recommended that you add the following entry to `.gitignore`.

```gitignore
tools/pqv_token.txt
```

---

## 2. Initial Setup on Windows

Perform this setup on your local PC, that is, the Windows PC on which you want to display PQViewer in a browser.

### 2.1 Clone the Repository

```bat
git clone https://github.com/mfukudaQED/PQViewer_Band_DOS.git
cd PQViewer_Band_DOS
```

### 2.2 Run the Windows Setup Script

```bat
tools\setup_windows_path.bat
```

This script automatically performs the following tasks.

- Detects the repository root
- Detects the `tools` directory
- Generates a fixed token in `tools\pqv_token.txt`
- Sets `PQV_TOKEN` as a Windows user environment variable
- Adds `tools` to the Windows user PATH
- Displays the setup command to be used on the remote side

After execution, a token similar to the following is displayed.

```text
Token:
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Use this token when setting up the remote side.

> Note: After setup, open a new Command Prompt, PowerShell, or Windows Terminal. PATH changes are not reflected in terminals that are already open.

---

## 3. Start the Agent on Windows

Open a new terminal and run the following command.

```bat
pqv_agent.bat
```

Alternatively, you may double-click the following file in Explorer.

```text
PQViewer_Band_DOS\tools\pqv_agent.bat
```

After startup, the local agent listens at the following URL.

```text
http://127.0.0.1:18765/
```

Do not close this terminal. If you close it, files can no longer be sent from the remote server.

---

## 4. Initial Setup on the Remote Side

Clone the same repository on the remote server.

```bash
git clone https://github.com/mfukudaQED/PQViewer_Band_DOS.git
cd PQViewer_Band_DOS
```

Use the token displayed during the Windows-side setup to run the setup on the remote side.

```bash
bash tools/setup_remote_path.sh --token PASTE_TOKEN_HERE
```

Example:

```bash
bash tools/setup_remote_path.sh --token xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

If you use bash, run the following command to apply the settings.

```bash
source ~/.bashrc
```

If you use fish, run the following command.

```fish
source ~/.config/fish/conf.d/pqviewer_remote_open.fish
```

After setup, check the following.

```bash
which pqv-open
echo $PQV_TOKEN
```

If the path to `pqv-open` and the token are displayed, the setup was successful.

---

## 5. SSH Tunnel Required When Connecting to the Remote Server

When connecting to the remote server, create an SSH reverse tunnel.

```bash
ssh -R 127.0.0.1:18765:127.0.0.1:18765 user@remote-host
```

If specifying this every time is inconvenient, add the following to `~/.ssh/config` on your local PC.

```sshconfig
Host myremote
    HostName remote-host
    User user
    RemoteForward 127.0.0.1:18765 127.0.0.1:18765
```

After that, you can connect with only the following command.

```bash
ssh myremote
```

---

## 6. Basic Usage

### 6.1 Open a Single File

Run this command on the remote side.

```bash
pqv-open band.dat
```

PQViewer opens in the browser on your local PC, and `band.dat` is loaded.

---

### 6.2 Open Multiple Files in Separate Viewers

```bash
pqv-open --separate band1.dat band2.dat
```

`--separate` explicitly specifies that the files should be opened as separate Viewer pages.

---

### 6.3 Open Multiple Files Together in a Single Viewer

Use this option when you want to load Band and DOS data into the same screen, for example.

```bash
pqv-open --same-view sample.BAND sample.DOS.Tetrahedron
```

A short option is also available.

```bash
pqv-open -m sample.BAND sample.DOS.Tetrahedron
```

---

### 6.4 Open a Named Viewer and Add Files Later

First, open a named Viewer.

```bash
pqv-open --open-target main
```

This Viewer waits under the name `main`.

Later, add a file to that Viewer.

```bash
pqv-open --target main new_band.dat
```

You can also add multiple files.

```bash
pqv-open --target main new_band.dat new_dos.dat
```

---

### 6.5 Use Multiple Named Viewers Separately

When opening multiple Viewers for comparison, use different names.

```bash
pqv-open --open-target compare1
pqv-open --open-target compare2
```

You can add different files to each Viewer.

```bash
pqv-open --target compare1 band_A.dat
pqv-open --target compare2 band_B.dat
```

---

### 6.6 Request a New Browser Window

```bash
pqv-open --open-target main --new-window
```

Or:

```bash
pqv-open --separate --new-window band1.dat band2.dat
```

However, whether this actually opens a new window or a new tab depends on the browser settings.

---

## 7. Typical Workflow

### On Windows

1. Start `pqv_agent.bat`.
2. Keep the terminal open.

```bat
pqv_agent.bat
```

### On the Remote Side

1. Log in with the SSH tunnel enabled.
2. Use `pqv-open`.

```bash
ssh myremote
pqv-open --open-target main
pqv-open --target main sample.BAND sample.DOS.Tetrahedron
```

---

## 8. Checking the Token

Run the following command on the Windows side.

```bat
tools\show_pqv_token.bat
```

The token and the command for remote setup are displayed.

---

## 9. Troubleshooting

### 9.1 `pqv-open: command not found`

The PATH settings on the remote side have not been applied.

For bash:

```bash
source ~/.bashrc
which pqv-open
```

For fish:

```fish
source ~/.config/fish/conf.d/pqviewer_remote_open.fish
which pqv-open
```

---

### 9.2 `curl: Failed to connect to 127.0.0.1 port 18765`

Check the following items.

- Whether `pqv_agent.bat` is running on the Windows side
- Whether the reverse tunnel was created when connecting via SSH
- Whether the port number matches `18765`

Example SSH tunnel:

```bash
ssh -R 127.0.0.1:18765:127.0.0.1:18765 user@remote-host
```

---

### 9.3 `403 Invalid token`

The tokens on the Windows side and the remote side do not match.

Check the token on the Windows side.

```bat
tools\show_pqv_token.bat
```

Run the setup again on the remote side.

```bash
bash tools/setup_remote_path.sh --token PASTE_TOKEN_HERE
source ~/.bashrc
```

---

### 9.4 Files Are Not Added with `--target`

Check whether the target named Viewer is open.

```bash
pqv-open --open-target main
```

Then add the file.

```bash
pqv-open --target main file.dat
```

If multiple Viewers with the same target name are open, the Viewer that polls first receives the file. In general, use only one Viewer for each target name.

---

## 10. Notes for Administrators

### 10.1 Files That Should Be Included in GitHub

```text
index.html
tools/pqv-open
tools/pqv_agent.py
tools/pqv_agent.bat
tools/setup_windows_path.bat
tools/setup_remote_path.sh
tools/show_pqv_token.bat
```

### 10.2 Files That Should Not Be Included in GitHub

```text
tools/pqv_token.txt
```

This is a secret token for each user.

Add the following entry to `.gitignore`.

```gitignore
tools/pqv_token.txt
```
