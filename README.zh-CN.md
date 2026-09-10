<h1 align="center">Namishu Calendar</h1>

<p align="center">可打印的月历，为你的计划留出空间。</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&amp;logo=python&amp;logoColor=white" alt="Python 3.10+">
  <a href="https://github.com/namishu/calendar/blob/main/LICENSE"><img src="https://img.shields.io/badge/Code-MIT-22A06B?style=flat" alt="代码许可：MIT">
  </a>
  <img src="https://img.shields.io/badge/PDF-A4_landscape-E05D44?style=flat" alt="PDF：A4 横向">
</p>

<p align="center"><a href="README.md">English</a> · <strong>简体中文</strong></p>

Namishu Calendar 生成简洁的月历，为手写计划、日程和提醒留出空间。
可以生成全年或单个月份的 PDF，每月一页。默认采用 A4 横向纸张，
月份和星期名称为英文，每周从周一开始。

<p align="center">
  <a href="https://github.com/namishu/calendar/blob/main/examples/calendar.pdf">
    <img src="examples/calendar.png" alt="2027 年 9 月月历，每周从周一开始，每个日期格内留有书写空间" width="800">
  </a>
</p>

[下载示例 PDF](https://github.com/namishu/calendar/raw/refs/heads/main/examples/calendar.pdf)，
使用 A4 纸按实际大小打印。

## 安装

需要 **Python 3.10+**。

使用 uv 或 pip 安装：

```bash
uv tool install namishu-calendar
```

```bash
python -m pip install namishu-calendar
```

两种方式都会提供 `namishu-calendar` 命令。默认字体和版式随安装包提供，
无需额外安装字体。

## 快速开始

生成**当前年份**从 1 月到 12 月的月历，保存为 `calendar.pdf`：

```bash
namishu-calendar
```

指定年份：

```bash
namishu-calendar --year 2027
```

添加 `--month`，生成**单个月份**：

```bash
namishu-calendar --year 2027 --month 9
```

省略 `--year` 时使用当前年份。通过 `-o` 指定输出路径：

```bash
namishu-calendar --year 2027 --month 9 -o calendars/september.pdf
```

生成完成后，命令会显示文件保存位置和页数。相对路径以当前工作目录为准，
不存在的上级目录会自动创建。如果输出路径已有 PDF 文件，会直接覆盖。

## 命令行选项

| 选项 | 用途 | 默认值 |
|---|---|---|
| `--year YEAR` | 年份，范围为 1–9999 | 当前年份 |
| `--month MONTH` | 只生成指定月份，范围为 1–12 | 全年 12 个月 |
| `-o, --output PATH` | PDF 保存路径 | `calendar.pdf` |
| `--config PATH` | 用于覆盖版式或字体设置的 YAML 文件 | 内置设置 |
| `--help` | 显示使用说明 | |
| `--version` | 显示已安装的版本 | |

## 自定义月历

只需填写想要修改的设置。例如，将以下内容保存为 `calendar.yaml`，
即可让每周从周日开始，并缩小左右边距：

```yaml
weekday:
  first_day: 6
layout:
  margin_left: 15
  margin_right: 15
```

```bash
namishu-calendar --year 2027 --month 9 --config calendar.yaml
```

未指定的设置保留默认值，包括内置字体。
可以下载[完整示例配置](https://github.com/namishu/calendar/blob/main/examples/calendar.yaml)，
查看所有设置及注释。该文件使用内置字体，下载后即可使用；
按需修改后，通过 `--config` 指定其本地路径。

| 设置 | 修改方式 |
|---|---|
| 纸张与边距 | `layout`：尺寸和边距，单位为毫米 |
| 月份名称 | `header.months`：按 1 月至 12 月排列的 12 个名称 |
| 星期名称 | `weekday.names`：按周一至周日排列的 7 个名称 |
| 每周起始日 | `weekday.first_day`：`0` 为周一，依次到 `6` 为周日 |
| 文字 | `header`、`weekday` 和 `day` 中的 `size`（单位为磅）与 `color` |
| 日期格 | `cell`：格间距、边框宽度、圆角半径和边框颜色 |
| 空白格 | `cell.hide_empty`：`0` 为边框完全显示，`1` 为隐藏 |
| 日期数字位置 | `day.align`：`LT` 左上、`RT` 右上、`LB` 左下、`RB` 右下、`C` 居中 |
| 自定义字体 | `font.path`：TrueType 字体路径，可使用相对于 YAML 文件的路径或绝对路径 |

除字号外，距离和尺寸的单位均为毫米。十六进制颜色值需加引号，例如 `"#5f667e"`。
月份和星期名称可以改为中文；内置的 Noto Sans SC 字体支持简体中文。
使用自定义字体时，请确保字体包含所需字符。设置无效或字体无法读取时，命令会报错。

## 许可证

代码和原创文档采用 [MIT 许可证](https://github.com/namishu/calendar/blob/main/LICENSE)。
内置的 Noto Sans SC 字体采用
[SIL Open Font License 1.1](https://github.com/namishu/calendar/blob/main/src/namishu_calendar/data/fonts/OFL.txt)，
其[说明文件](https://github.com/namishu/calendar/blob/main/src/namishu_calendar/data/fonts/NOTICE.txt)
记录了字体的版权归属和来源信息。
生成的月历可以打印、分享、修改和销售。
