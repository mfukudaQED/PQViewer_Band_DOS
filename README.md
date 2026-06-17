# Band + DOS Viewer

A browser-based interactive viewer for electronic band structures, density of states (DOS/PDOS), and unfolded band data, which are generated in [OpenMX](https://www.openmx-square.org/).
The viewer is distributed as a single HTML application and is designed for quick inspection, comparison, analysis, and publication-oriented figure preparation.

## Features

- **Band structure and DOS visualization**
  - Display band structures and DOS side by side.
  - Load multiple band, DOS, and PDOS series.
  - Manage visibility, ordering, labels, and styles for individual series.

- **Supported electronic-structure workflows**
  - Band structure files.
  - DOS and PDOS files.
  - Unfolded band data, including scatter and intensity-map visualization.
  - OpenMX input files for extracting labels and related metadata.

- **Interactive analysis**
  - Zoom and pan by mouse operations.
  - Crosshair readout for cursor coordinates.
  - Mark points on plots and compare selected points using energy and momentum differences.
  - Band-gap analysis, including VBM/CBM marking.
  - DOS/PDOS integration over a selected energy window.
  - Energy-zero/Fermi-level shift controls for all data, file groups, and unfolded-band data.

- **Publication-oriented customization**
  - Line color, width, dash style, point marker, and marker size.
  - Axis labels, ticks, minor ticks, grids, and zero lines.
  - Independent Band and DOS legends with adjustable font size, box, position, padding, and transparency.
  - Panel labels such as `(a)` and `(b)`.
  - Custom, light, and dark color themes.
  - Font and UI font controls.
  - MathJax-compatible text for scientific labels and legends.

- **Unfolded band visualization**
  - Overlay unfolded-band data on a band plot.
  - Choose scatter, intensity map, or combined display mode.
  - Configure colormap, broadening function, intensity scaling, grid size, cutoff, gamma, alpha, and colorbar.
  - Select unfolded weights by column, metadata group, or rule-based filters such as species, atoms, shells, and orbitals.

- **Export and reproducibility**
  - Export combined Band + DOS figures as PNG.
  - Export Band-only and DOS-only PNG images.
  - Select PNG scale for high-resolution output.
  - Export and import JSON configuration files to reproduce plot settings.

## Supported file types

The viewer accepts files by drag and drop. Typical supported inputs include:

- `*.BAND`
- `*.BANDDAT*`
- `*.DOS.*`
- `*.PDOS.*`
- `*.unfold_*`
- OpenMX input files, for example `*.dat` and `*.dat#`
- JSON configuration files exported from this viewer

Exact parsing behavior depends on the data layout and metadata available in the input files.

## Quick start

1. Open the HTML file in a modern web browser.
2. Drag and drop one or more supported files onto the drop area.
3. Use the **Control Panel** to adjust visibility, style, axes, legends, analysis options, and unfolded-band settings.
4. Use mouse operations or keyboard shortcuts to inspect the plot.
5. Export the result as PNG or save the current state as a JSON configuration file.

No server-side processing is required for normal use. Data are handled in the browser session.

## Keyboard and mouse shortcuts

| Operation | Action |
| --- | --- |
| Left drag | Rectangular zoom |
| Right drag | Pan |
| Double click | Reset zoom |
| Mouse wheel | Zoom |
| Shift + mouse wheel | Pan |
| `z` | Set zoom mode to x + y |
| `x` | Set zoom mode to x only |
| `y` | Set zoom mode to y only |
| `r` | Reset zoom |
| `m` | Clear marked points |
| `l` | Toggle legends |
| `g` | Toggle grids |
| `p` | Export PNG |
| `?` | Show shortcut help |
| `Esc` | Close popup/help |

## Configuration workflow

The viewer can export its current state as a JSON configuration file. This is useful for:

- Reproducing figure settings.
- Sharing visualization presets with collaborators.
- Restoring a previous analysis session.
- Preparing a series of figures with consistent visual style.

To restore a session, import the exported JSON configuration file into the viewer.

## Dependencies

The application is implemented as static HTML, CSS, and JavaScript using HTML5 Canvas. It does not require a backend server.

The bundled HTML may load external resources such as:

- MathJax, for rendering mathematical labels and legends.
- Web fonts, depending on the selected UI/font settings.

For fully offline use, consider hosting these resources locally or modifying the HTML to remove CDN dependencies.

## Browser compatibility

Use a recent version of a modern desktop browser, such as:

- Microsoft Edge
- Google Chrome / Chromium
- Mozilla Firefox
- Safari

Large unfolded-band or dense PDOS datasets may require additional memory and rendering time.

## Repository layout

This repository is designed to be published as a GitHub Pages project site named
`PQViewer_Band_DOS`.

A recommended repository layout is:

```text
PQViewer_Band_DOS/
├── index.html
├── README.md
└── LICENSE
```

- `index.html`: the main Band + DOS viewer application.
- `README.md`: documentation for users and developers.
- `LICENSE`: the Mozilla Public License 2.0 license text.

The viewer is available at:

```text
https://mfukudaQED.github.io/PQViewer_Band_DOS/
```


## Deployment

Because the viewer is a static web application, it can be published with any static hosting service, for example:

- GitHub Pages
- GitLab Pages
- A university web server
- Any standard static web host

For GitHub Pages, place the HTML file as `index.html` in the published branch or directory.

## Privacy note

The viewer is intended to process dropped files locally in the browser. If you host the application as a static page, the input data are not intentionally uploaded to a server by the viewer itself. Users should still follow their institution's data-handling rules and verify the deployed version before using confidential data.


## License

This project is licensed under the **Mozilla Public License 2.0 (MPL-2.0)**.

See the `LICENSE` file for the full license text.

Under MPL-2.0, modified source files covered by the license must remain available under MPL-2.0 when distributed. This README is not legal advice; consult the MPL-2.0 text for the exact terms.


## AI-Assisted Development

This viewer was developed with assistance from GPT-5.5 Think.
Parts of the source code were generated with AI assistance and were reviewed, modified, and maintained by the project author.

## Citation / acknowledgement

If this viewer helps prepare figures or analyze data for a publication,
please consider citing or acknowledging the repository according to the citation information provided by the project maintainers.


