"""中文营养课程生成器 CLI —— Typer 入口"""

import typer
import json
from pathlib import Path
from src.schemas.lesson import 生成请求
from src.pipeline.generator import 生成课程, 导出全部, 从PubMed生成课程

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
    max_results: int = typer.Option(10, "--max-results", "-m", help="PubMed 最大检索数"),
    date_from: str = typer.Option(None, "--date-from", help="PubMed 检索起始年份"),
    date_to: str = typer.Option(None, "--date-to", help="PubMed 检索结束年份"),
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
        max_results=max_results,
    )

    # 根据证据来源选择生成器
    if evidence_source == "pubmed":
        typer.echo("🔬 正在检索 PubMed 文献...")
        结果 = 从PubMed生成课程(请求, date_from=date_from, date_to=date_to)
    else:
        课程 = 生成课程(请求)
        结果 = 导出全部(课程, output_dir)

    typer.echo(f"\n✅ 课程生成完成！")
    for name, path in 结果.items():
        if path:
            typer.echo(f"   {name}: {path}")

    # 验证
    from src.pipeline.validator import 验证课程
    if isinstance(结果, dict):
        课程 = 结果.get("课程规范")
        if isinstance(课程, str):  # file path
            try:
                from src.schemas.lesson import 课程规范 as 课程规范模型
                课程数据 = json.loads(Path(课程).read_text(encoding='utf-8'))
                课程 = 课程规范模型(**课程数据)
            except Exception:
                课程 = None
    if isinstance(结果, dict) and 课程:
        通过, 问题 = 验证课程(课程)
        if 通过:
            typer.echo(f"\n🟢 质量检查通过，无问题。")
        else:
            typer.echo(f"\n🟡 质量检查发现 {len(问题)} 个问题：")
            for q in 问题:
                typer.echo(f"   ⚠️ {q}")


@app.command()
def retrieve(
    topic: str = typer.Option(..., "--topic", "-t", help="检索主题"),
    max_results: int = typer.Option(10, "--max-results", "-m", help="最大结果数"),
    output: str = typer.Option("output/pubmed-preview", "--output", "-o", help="输出目录"),
):
    """仅检索 PubMed 文献，预览证据（不生成课件）"""
    from src.pubmed.client import PubMedClient

    typer.echo(f"🔬 正在检索 PubMed：{topic}")
    client = PubMedClient()
    结果 = client.搜索(topic, max_results=max_results)

    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)

    # 保存检索结果
    (out / "检索关键词.json").write_text(json.dumps({"主题": topic, "查询语句": 结果.查询.最终查询语句}, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / "pubmed_raw.json").write_text(json.dumps(结果.原始搜索响应, ensure_ascii=False, indent=2), encoding='utf-8')
    (out / "pubmed_records.json").write_text(json.dumps([r.model_dump() for r in 结果.文献列表], ensure_ascii=False, indent=2, default=str), encoding='utf-8')

    typer.echo(f"\n✅ 检索完成！")
    typer.echo(f"   找到 {len(结果.文献列表)} 篇文献，{len(结果.证据摘要列表)} 条证据摘要")
    typer.echo(f"\n📁 输出：{out}/")
    for r in 结果.文献列表[:5]:
        title = r.标题 or "无标题"
        typer.echo(f"   PMID:{r.pmid}  {title[:80]}...")


@app.command()
def version():
    """显示版本"""
    typer.echo("中文营养课程生成器 v0.1.0")


if __name__ == "__main__":
    app()
