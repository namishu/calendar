<h1 align="center">Namishu Calendar</h1>

<p align="center">可打印的月历，为你的计划留出空间。</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&amp;logo=python&amp;logoColor=white" alt="Python 3.10+">
  <a href="https://github.com/namishu/calendar/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-22A06B?style=flat" alt="License: MIT">
  </a>
  <img src="https://img.shields.io/badge/PDF-A4_landscape-E05D44?style=flat" alt="PDF：A4 横向">
</p>

<p align="center"><a href="README.md">English</a> · <strong>简体中文</strong></p>

<p align="center">
  <a href="https://github.com/namishu/calendar/blob/main/examples/calendar.pdf">
    <img src="examples/calendar.png" alt="2027 年 9 月月历，每周从周一开始，每个日期格内留有书写空间" width="560">
  </a>
</p>

Namishu Calendar 是一个生成可打印月历的命令行小工具。指定年份或月份，
就能得到每月一页的 PDF，每个日期格里都留有手写空间。你可以把它贴在冰箱上，
记录一家人的日程；放在教室公告栏里，标注班级活动；也可以摆在书桌旁，安排学习计划。

它会自动排好日期和版面，省去自己画表格、核对星期或修改旧模板的工夫，
需要时生成一份，打印出来就能用。默认版式为 A4 横向，使用英文月份和星期名称，
每周从周一开始。你也可以按自己的习惯调整文字、每周起始日、颜色和边距。

<p align="center">
  示例 PDF 文件：<a href="examples/calendar.pdf">月历打印版</a>
</p>

## 安装

需要 **Python 3.10+**。

使用 uv 或 pip 安装：

```bash
uv tool install namishu-calendar
```

```bash
python -m pip install namishu-calendar
```

两种方式都会提供 `namishu-calendar` 命令。Noto Sans Light 字体和默认版式随安装包提供，
生成英文月历无需额外安装字体。

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

使用 A4 纸按实际大小打印。

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
weekdays:
  week_start: sunday
page:
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
| 纸张与边距 | `page`：尺寸和边距，单位为毫米 |
| 月份名称 | `title.months`：按 1 月至 12 月排列的 12 个名称 |
| 星期名称 | `weekdays.names`：按周一至周日排列的 7 个名称 |
| 每周起始日 | `weekdays.week_start`：`monday` 至 `sunday`，分别对应周一至周日 |
| 文字 | `title`、`weekdays` 和 `day_numbers` 中的 `font_size`（单位为磅）与 `color` |
| 日期格 | `grid`：格间距、边框宽度、圆角半径和边框颜色 |
| 空白格 | `grid.empty_opacity`：`0` 为隐藏，`1` 为边框完全显示 |
| 日期数字 | `day_numbers.position`：`top_left` 左上、`top_right` 右上、`bottom_left` 左下、`bottom_right` 右下、`center` 居中；`padding` 控制数字与边框内沿的距离 |
| 垂直间距 | `title.gap_after` 和 `weekdays.gap_after`：每行文字下方的留白，从可见字形边界计算 |
| 自定义字体 | `font`：TrueType 字体路径，可使用相对于 YAML 文件的路径或绝对路径 |

除字号外，距离和尺寸的单位均为毫米。日期数字居中时忽略 `padding`；
网格间距从相邻边框的外沿计算。文字或日期格空间不足时，程序会在创建或覆盖 PDF 前报错。十六进制颜色值需加引号，例如 `"#5f667e"`。
内置的 Noto Sans Light 字体支持默认英文标签，不包含中文字形。
生成中文月历时，请在 YAML 中修改月份和星期名称，并指定支持中文的字体，
例如 Noto Sans SC。

使用自定义字体时，在 YAML 配置中添加字体路径即可：

```yaml
font: fonts/MyFont.ttf
```

字体路径相对于 YAML 文件所在目录，也可以使用绝对路径。
字体会嵌入 PDF，接收文件的人无需安装该字体。
设置无效、字体无法读取或缺少所需字符时，命令会报错。

## 许可证

代码和原创文档采用 [MIT 许可证](https://github.com/namishu/calendar/blob/main/LICENSE)。
内置的 Noto Sans Light 字体采用
[SIL Open Font License 1.1](https://github.com/namishu/calendar/blob/main/src/namishu_calendar/data/OFL.txt)，
同一文件中也记录了字体的版权归属和来源信息。
生成的月历可以打印、分享、修改和销售。
