"""
数据导入导出页面 — CSV 导出、CSV 导入、数据库备份。
"""

import streamlit as st

from src.db import init_db
from src.import_export import (
    export_mistakes_csv, import_mistakes_csv,
    export_review_records_csv, backup_database,
)
import os

init_db()


def main():
    st.title("📥 数据导入导出")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 导出错题 CSV", "📥 导入错题 CSV",
        "📤 导出复习记录 CSV", "💾 数据库备份",
    ])

    with tab1:
        st.subheader("导出全部错题为 CSV")
        st.caption("将系统中所有错题导出为 CSV 文件，可在 Excel 中打开编辑。")
        if st.button("📤 生成错题 CSV", type="primary"):
            csv_content = export_mistakes_csv()
            st.download_button(
                label="⬇️ 下载错题 CSV",
                data=csv_content,
                file_name="错题库_导出.csv",
                mime="text/csv",
            )
            st.success("CSV 已生成，点击上方按钮下载。")

    with tab2:
        st.subheader("从 CSV 导入错题")
        st.caption("上传包含错题数据的 CSV 文件。CSV 必须包含「题目标题」「科目」列。")
        st.markdown("""
        **CSV 列名参考：**
        `题目标题, 科目, 章节, 题目内容, 错误原因, 正确解法, 关键知识点, 来源, 难度, 是否收藏, 是否熟练, 备注`
        """)

        uploaded = st.file_uploader("选择 CSV 文件", type="csv", key="import_csv")
        if uploaded is not None:
            csv_str = uploaded.getvalue().decode("utf-8-sig")
            # 预览前 5 行
            st.caption("文件预览（前 500 字符）：")
            st.text(csv_str[:500])

            if st.button("📥 开始导入", type="primary"):
                success, errors = import_mistakes_csv(csv_str)
                if success > 0:
                    st.success(f"成功导入 {success} 道错题！")
                if errors:
                    st.warning(f"以下 {len(errors)} 行导入失败：")
                    for e in errors:
                        st.caption(f"- {e}")
                if success == 0 and not errors:
                    st.info("未检测到有效数据。请检查 CSV 格式。")

    with tab3:
        st.subheader("导出复习记录为 CSV")
        if st.button("📤 生成复习记录 CSV", type="primary"):
            csv_content = export_review_records_csv()
            st.download_button(
                label="⬇️ 下载复习记录 CSV",
                data=csv_content,
                file_name="复习记录_导出.csv",
                mime="text/csv",
            )
            st.success("CSV 已生成，点击上方按钮下载。")

    with tab4:
        st.subheader("备份 SQLite 数据库")
        st.caption("创建当前数据库的完整副本。")

        # 显示数据库信息
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "review.db")
        if os.path.exists(db_path):
            size_kb = os.path.getsize(db_path) / 1024
            st.info(f"数据库位置：{db_path}\n\n大小：{size_kb:.1f} KB")

        if st.button("💾 创建备份", type="primary"):
            backup_path = backup_database()
            st.success(f"备份已创建：{backup_path}")

        # 列出已有备份
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "backups")
        if os.path.exists(backup_dir):
            backups = sorted(os.listdir(backup_dir), reverse=True)
            if backups:
                st.markdown("**已有备份：**")
                for b in backups[:10]:
                    st.caption(f"- {b}")


if __name__ == "__main__":
    main()
