"""中文营养课程生成器 CLI —— Typer 入口"""

import typer
from src.schemas.lesson import 生成请求
from src.pipeline.generator import 生成课程, 导出全部

app = typer.Typer(
    name="nutrition-lesson-generator-zh",
    help="中文营养课程生成器 —— 将营养主题转化为结构化课件包",
)


@app.command()
def generate(
    topic: str = typer.Option(..., "--topic", "-t", help="营养主题"),
    audience: str = typer.Option("普通成年人", "--audience", "-a", help="目标听众"),
    language: str = typer.Option("zh", "--language", "-l", help="输出语言（默认中文）"),
    duration: int = typer.Option(30, "--duration", "-d", help="课时长度（分钟）"),
    output_dir: str = typer.Option("output", "--output-dir", "-o", help="输出目录"),
    evidence_source: str = typer.Option("mock", "--evidence-source", "-e", help="证据来源：mock/pubmed"),
):
    """生成中文营养课程"""
    typer.echo(f"🎓 正在生成中文营养课程：{topic}")
    typer.echo(f"   目标听众：{audience} | 时长：{duration}分钟 | 证据模式：{evidence_source}")

    请求 = 生成请求(
        主题=topic,
        目标听众=audience,
        语言=language,
        课时分钟=duration,
        输出目录=output_dir,
        证据来源=evidence_source,
    )

    课程 = 生成课程(请求)
    结果 = 导出全部(课程, output_dir)

    typer.echo(f"\n✅ 课程生成完成！")
    typer.echo(f"   总页面数：{len(课程.页面列表)}")
    typer.echo(f"   引用数：{len(课程.引用列表)}")
    typer.echo(f"\n📁 输出文件：")
    for name, path in 结果.items():
        typer.echo(f"   {name}: {path}")

    # 验证
    from src.pipeline.validator import 验证课程
    通过, 问题 = 验证课程(课程)
    if 通过:
        typer.echo(f"\n🟢 质量检查通过，无问题。")
    else:
        typer.echo(f"\n🟡 质量检查发现 {len(问题)} 个问题：")
        for q in 问题:
            typer.echo(f"   ⚠️ {q}")


@app.command()
def version():
    """显示版本"""
    import importlib.metadata
    try:
        v = importlib.metadata.version("nutrition-lesson-generator-zh")
    except Exception:
        v = "0.1.0"
    typer.echo(f"中文营养课程生成器 v{v}")


if __name__ == "__main__":
    app()
