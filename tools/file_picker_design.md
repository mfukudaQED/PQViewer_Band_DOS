# File Picker 設計書

## 1. 目的

この File Picker は、Viewer に読み込んだローカルファイルを管理し、必要に応じて**同じファイルの最新内容を再読込**するための UI / state 管理モジュールである。

主な目的は以下である。

- ファイル選択または drag & drop で読み込んだファイルをリスト化する。
- File System Access API が利用可能な場合、`FileSystemFileHandle` を保持する。
- reload 時に `handle.getFile()` を呼び、ディスク上の最新状態を再取得する。
- reload 前に同名ファイル由来の series を削除する。
- reload 後も線色・線種・表示状態などの style を維持する。

`FileSystemFileHandle.getFile()` は、ハンドルが表すエントリのディスク上の現在状態を表す `File` を返す API である。そのため、外部エディタや計算ジョブで更新された内容を reload 時に取得できる。

---

## 2. 前提

### 2.1 対象ブラウザ

- Chrome / Edge など Chromium 系ブラウザでは `window.showOpenFilePicker()` を使う。
- 非対応環境では通常の `<input type="file">` に fallback する。
- File System Access API は secure context、つまり HTTPS または localhost などでの利用を前提とする。
- Firefox / Safari ではローカルディスク picker が使えない場合があり、その場合は fallback 動作になる。

### 2.2 Viewer 側の前提

File Picker は汎用化のため、Viewer 側に adapter 的な関数群を要求する設計にする。

```js
const adapter = {
  loadFiles: async files => {},
  removeSeriesForFiles: files => {},
  snapshotSeriesForFiles: files => [],
  applySeriesSnapshots: (files, snapshots) => {},
  tagSeriesForFiles: files => {},
  redraw: () => {},
  setStatus: text => {}
};
```

PQViewer では、これらを既存の `files()`, `S.band`, `S.dos`, `S.unfold.items` に対して実装している。

---

## 3. UI 構成

Control Panel 内に以下の UI を置く。

```text
File Picker
[Open files] [Reload loaded files] [Clear list]

[x] ↻ case.BAND
[x] ↻ case.DOS.Tetrahedron
[x] △ fallback_file.BAND
```

### 3.1 UI 要素

| 要素 | 役割 |
|---|---|
| `Open files` | File System Access API でファイルを開く。非対応なら fallback input を開く。 |
| `Reload loaded files` | チェック済みファイルを最新内容で再ロードする。 |
| `Clear list` | File Picker が保持するロード済みファイルリストをクリアする。 |
| loaded file list | ロード済みファイルの一覧。チェックボックス付き。 |
| `↻` | handle があり、reload 時に最新内容を取得できる。 |
| `△` | 通常の `File` のみ。reload はできるが、外部更新の反映は保証しない。 |

---

## 4. State model

File Picker は内部に以下の state を持つ。

```js
const CP_FILE_PICKER_TRACK = {
  items: new Map()
};
```

各 item は以下の構造を持つ。

```js
{
  key: string,
  file: File,
  handle: FileSystemFileHandle | null,
  name: string,
  path: string,
  source: string,
  size: number,
  lastModified: number,
  canRefresh: boolean
}
```

### 4.1 各フィールド

| フィールド | 意味 |
|---|---|
| `key` | File Picker 内での識別子。 |
| `file` | 直近ロード時の `File`。 |
| `handle` | File System Access API の file handle。 |
| `name` | ファイル名。 |
| `path` | ブラウザから取得可能なパス風ラベル。 |
| `source` | `picker-handle`, `drop-handle`, `load` など。 |
| `size` | ファイルサイズ。 |
| `lastModified` | 最終更新時刻。 |
| `canRefresh` | `handle.getFile()` で最新取得できるか。 |

---

## 5. 基本フロー

## 5.1 Open files

```text
User clicks Open files
  ↓
showOpenFilePicker({ multiple: true })
  ↓
FileSystemFileHandle[] を取得
  ↓
各 handle.getFile() で File を取得
  ↓
File と handle を tracking list に登録
  ↓
Viewer の loadFiles(files) を呼ぶ
```

非対応ブラウザでは、hidden な `<input type="file" multiple>` を開く。

---

## 5.2 Drag & drop

```text
User drops files
  ↓
dataTransfer.files を取得
  ↓
可能なら dataTransfer.items[i].getAsFileSystemHandle() を試す
  ↓
handle が取れたファイルは canRefresh=true
  ↓
handle が取れないファイルは fallback File として登録
  ↓
Viewer の loadFiles(files) を呼ぶ
```

---

## 5.3 Reload loaded files

```text
User clicks Reload loaded files
  ↓
checked entries を取得
  ↓
handle があるものは handle.getFile() で最新 File を取得
  ↓
既存 series の style snapshot を保存
  ↓
同名ファイル由来の series を削除
  ↓
Viewer の loadFiles(freshFiles) を呼ぶ
  ↓
新規 series に style snapshot を復元
  ↓
色カウンターなどを reload 前の値に戻す
```

---

## 6. Style 維持設計

reload 時に線色が変わる原因は、Viewer の loader が新規 series として再追加するときに、色カウンターを使って色を再割当てするためである。

そのため、File Picker 側では reload 処理を以下のように分ける。

### 6.1 reload 前

対象ファイルに対応する series を探し、style snapshot を保存する。

保存対象は以下。

```js
{
  kind,
  fileName,
  path,
  label,
  glabel,
  legend,
  spin,
  source,
  color,
  width,
  dash,
  point,
  psize,
  visible
}
```

### 6.2 reload 中

対象ファイル由来の series を削除する。

```text
S.band = S.band から対象ファイル由来 series を除外
S.dos  = S.dos から対象ファイル由来 series を除外
S.unfold.items も対象 item を除外
```

### 6.3 reload 後

新しく作られた series と snapshot を照合する。

照合には以下を使う。

- `label`
- `spin`
- `source`
- `glabel`
- `fileName`
- `legend`

一致度が最も高い snapshot を適用する。

### 6.4 counter 復元

reload 前に以下を保存する。

```js
const savedCounters = {
  bandCi: S.bandCi,
  dosCi: S.dosCi
};
```

reload 後に戻す。

```js
S.bandCi = savedCounters.bandCi;
S.dosCi = savedCounters.dosCi;
```

これにより、reload によって色カウンターが進んでしまい、次に新しいファイルを開いたときの色割当てが変わる問題を抑制する。

---

## 7. Viewer 側 adapter requirements

この File Picker を他の viewer に転用する場合、最低限以下を viewer 側で差し替える。

| 関数 | 役割 |
|---|---|
| `loadFiles(files)` | ファイル群を viewer に読み込む。 |
| `removeSeriesForFiles(files)` | 対象ファイル由来の series を削除する。 |
| `snapshotSeriesForFiles(files)` | reload 前の style を保存する。 |
| `applySeriesSnapshots(files, snapshots)` | reload 後に style を戻す。 |
| `tagSeriesForFiles(files)` | series に file path / file name を紐付ける。 |
| `redraw()` | Viewer を再描画する。 |
| `setStatus(text)` | UI に状態メッセージを表示する。 |

---

## 8. 他 viewer へ移植する場合の推奨構造

File Picker 部分は、可能であれば独立モジュール化する。

```js
class ViewerFilePicker {
  constructor(adapter) {
    this.adapter = adapter;
    this.items = new Map();
  }
}
```

adapter は次の形にする。

```js
const adapter = {
  loadFiles: async files => {},
  removeSeriesForFiles: files => {},
  snapshotSeriesForFiles: files => [],
  applySeriesSnapshots: (files, snapshots) => {},
  tagSeriesForFiles: files => {},
  redraw: () => {},
  setStatus: text => {}
};
```

こうしておくと、PQViewer 以外でも以下のような viewer に再利用しやすくなる。

- band viewer
- DOS viewer
- PDOS viewer
- unfold viewer
- CSV viewer
- spectrum viewer
- image viewer

---

## 9. 制限事項

- 通常の browser file input では、外部エディタで更新された最新内容を確実には取得できない。
- 最新取得には `FileSystemFileHandle` が必要である。
- `showOpenFilePicker()` はユーザー操作から呼び出す必要がある。
- secure context が必要である。
- 完全な絶対パスはブラウザのセキュリティ制約上、基本的には取得できない。
- drag & drop で handle が取れるかどうかはブラウザ実装に依存する。
- File Picker はファイル監視ではないため、reload はユーザー操作で行う。
- 自動反映したい場合は、将来的に polling または local helper が必要である。

---

## 10. 今回の PQViewer 実装での対応関数

今回の実装では、主に以下を追加している。

```text
cpOpenFilesWithHandles()
cpReloadTrackedFiles()
cpFilesFromEntries()
cpRemoveSeriesForFiles()
cpSnapshotSeriesForFiles()
cpApplySeriesSnapshots()
cpTagSeriesForFiles()
cpRememberFiles()
cpRememberHandlesFromDataTransfer()
```

要点は、**File Picker はファイル取得と reload orchestration を担当し、Viewer 固有の series 削除・style 復元は adapter 的な関数群に閉じ込める**という設計である。

この分離を保つと、他の viewer に移植しやすくなる。
