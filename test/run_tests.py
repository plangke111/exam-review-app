"""回归测试脚本 —— 跑全部17个样本,每个3次,输出统计结果"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json, sys, os, time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.essay_grader import EnglishGrader, PoliticsGrader

TESTS = [
    # === 英语一大作文 ===
    {"id":"E-L-01","type":"english_big","exam":"英语一","max":20,"target":8,"low":7,"high":9,
     "prompt":"一幅图展示居民在家附近的新公园散步、锻炼；配套图表显示某市近三年公园数量持续增加。写160-200词，简要描述图画和图表，解释其含义并发表看法。",
     "answer":"The picture shows that some people are walking and doing exercise in a park near their homes. The chart also shows the number of parks in the city grows in recent three years. It is a good change for citizens.\n\nNowadays, people are busy with work and study, so they need a place to relax. More parks can give people fresh air and chances to exercise. It also make the city more beautiful. However, building parks need much money and some people may not use them very often. In my opinion, the government should build more parks and also keep them clean.\n\nIn conclusion, parks are important for city life. They can improve people's health and make the environment better. We should protect public facilities and do not throw rubbish in parks."},

    {"id":"E-L-02","type":"english_big","exam":"英语一","max":20,"target":11,"low":10,"high":12,
     "prompt":"一幅图展示居民在家附近的新公园散步、锻炼；配套图表显示某市近三年公园数量持续增加。写160-200词，简要描述图画和图表，解释其含义并发表看法。",
     "answer":"As is illustrated in the picture, several residents are enjoying a newly built park near their community. Some are walking, while others are exercising in a fitness area. The accompanying chart indicates that the number of parks in the city has risen steadily during the past three years.\n\nThis change reflects the growing attention paid to public health and urban living conditions. Parks provide citizens with convenient places to exercise, communicate with neighbors and escape from the pressure of daily life. They also improve the environment by adding green space to crowded cities. Nevertheless, simply increasing the number of parks is not enough. Some facilities may be poorly maintained, and certain parks may not meet the needs of elderly people or children.\n\nTherefore, local governments should not only construct more parks but also improve their management. Citizens, for their part, should use public facilities properly and help keep these places clean. In this way, urban parks can truly become shared spaces that improve the quality of life."},

    {"id":"E-L-03","type":"english_big","exam":"英语一","max":20,"target":16,"low":15,"high":17,
     "prompt":"一幅图展示居民在家附近的新公园散步、锻炼；配套图表显示某市近三年公园数量持续增加。写160-200词，简要描述图画和图表，解释其含义并发表看法。",
     "answer":"The drawing portrays residents exercising and chatting in a neighborhood park, while the accompanying chart records a continuous rise in the number of urban parks over the past three years. Taken together, the two images reveal a welcome shift in city development: public space is increasingly being treated as a basic component of a healthy life rather than as decorative land.\n\nThe expansion of parks produces benefits that cannot be measured merely by counting trees. Accessible green spaces encourage regular exercise, reduce stress and create opportunities for interaction among people who might otherwise remain strangers in the same community. More importantly, they reflect a people-centered approach to urban planning. Yet quantity alone is an incomplete indicator. A park located far from residential areas, poorly maintained or inaccessible to children and older residents may contribute little to public well-being.\n\nAccordingly, city authorities should combine expansion with careful planning, long-term maintenance and barrier-free design. Residents should also respect shared facilities and participate in community activities. When construction and responsible use reinforce each other, urban parks can improve both the physical environment and the social fabric of a city."},

    {"id":"E-L-04","type":"english_big","exam":"英语一","max":20,"target":9,"low":8,"high":10,
     "prompt":"图画展示乡村端午节龙舟活动，参赛者奋力划船，岸边群众观看；主题指向传统文化活动重新受到关注。写160-200词，描述图画、解释寓意并评论。",
     "answer":"In the picture, many people are watching a dragon boat race in a village. The players are trying their best and the people near the river look very excited. This activity is held during the Dragon Boat Festival and shows that traditional culture becomes popular again.\n\nTraditional festivals are important because they tell us where we come from. However, some young people are more interested in foreign festivals and know little about Chinese traditions. If this situation continues, some customs may disappear in the future. Holding activities such as dragon boat races can make traditional culture more interesting and attract young people.\n\nIn my opinion, schools and communities should organize more cultural activities. The media can also introduce the history behind traditional festivals. At the same time, we should not only take photos or watch shows, but understand the real meaning of these traditions. In this way, traditional culture can be protected and passed to the next generation."},

    {"id":"E-L-05","type":"english_big","exam":"英语一","max":20,"target":17,"low":16,"high":18,
     "prompt":"图画展示乡村端午节龙舟活动，参赛者奋力划船，岸边群众观看；主题指向传统文化活动重新受到关注。写160-200词，描述图画、解释寓意并评论。",
     "answer":"The drawing presents a lively dragon-boat race in a village: rowers move in rhythm, spectators crowd the riverbank, and a traditional festival becomes a shared public event. What deserves attention is not merely the excitement of the competition, but the renewed enthusiasm for cultural traditions that it represents.\n\nTraditional culture survives only when it remains connected with contemporary life. Activities such as dragon-boat racing transform historical memory from something read in textbooks into an experience that people can see, join and discuss. They strengthen community ties and give younger generations a vivid sense of cultural identity. Nevertheless, cultural revival should not be reduced to commercial performances or decorative symbols. Without an understanding of the values, stories and social bonds behind a custom, popularity may be temporary.\n\nTo achieve meaningful inheritance, schools can explain the historical background of festivals, communities can invite residents to participate, and digital media can present traditions in forms attractive to young audiences. Innovation is valuable when it helps people approach the substance of a tradition rather than replacing it. Only through informed participation can traditional culture remain both authentic and alive."},

    # === 英语二大作文 ===
    {"id":"E-L-06","type":"english_big","exam":"英语二","max":15,"target":7,"low":6,"high":8,
     "prompt":"图表展示某高校学生参加劳动实践课后的主要收获，包括掌握劳动技能、增强合作意识、体会劳动价值等类别。写约150词，描述数据、解释现象并评论。",
     "answer":"The chart shows the main benefits students get from a labor practice course. Many students say they learned useful skills, and others think the course improves teamwork or helps them understand the value of labor. This result shows that labor education is helpful.\n\nThere are several reasons. First, students usually spend much time in classrooms, so they have few chances to do practical work. Second, group tasks can teach them how to cooperate with others. Labor also makes students know that daily products are not easy to get. However, some courses may only ask students to finish simple tasks, which cannot give them deep experience.\n\nIn my opinion, universities should provide more meaningful labor activities and connect them with students' majors. Teachers should not only check the final result but also guide students during the process. In this way, labor courses can help students develop both practical ability and a responsible attitude."},

    {"id":"E-L-07","type":"english_big","exam":"英语二","max":15,"target":11,"low":10,"high":12,
     "prompt":"图表展示某高校学生参加劳动实践课后的主要收获，包括掌握劳动技能、增强合作意识、体会劳动价值等类别。写约150词，描述数据、解释现象并评论。",
     "answer":"The chart summarizes what students gained from a university labor-practice course. Practical skills account for the largest share, while teamwork, a stronger sense of responsibility and a better understanding of the value of labor are also frequently reported. The figures suggest that labor education can influence students in several dimensions rather than merely teaching them how to complete a task.\n\nThis outcome is understandable. Many undergraduates receive systematic academic training but have limited opportunities to solve concrete problems with their hands. Well-designed labor activities require planning, cooperation and persistence, thereby linking knowledge with action. They can also correct the mistaken belief that ordinary work is unimportant. However, repetitive or purely symbolic tasks may turn the course into a formality.\n\nUniversities should therefore design authentic projects, provide clear guidance and assess both the process and the result. When labor education is connected with community service or students' fields of study, it can cultivate practical competence as well as respect for work."},

    # === 英语小作文 ===
    {"id":"E-S-01","type":"english_small","exam":"英语一","max":10,"target":5,"low":4,"high":6,
     "prompt":"一名国际学生要做关于中国古代科学家的课堂口头报告，来信向你征求建议。请回复，推荐一位科学家并说明可介绍的内容。约100词。",
     "answer":"Dear Jack,\n\nI am glad to know that you will make a report about an ancient Chinese scientist. I suggest you introduce Zhang Heng. He was a famous scientist in ancient China and made important achievements in astronomy. He also invented a machine to find earthquakes, which was very advanced at that time.\n\nYou can first talk about his life, and then explain his inventions and influence. It is better to use some pictures because they can make your report easy to understand. I hope my advice can help you.\n\nYours,\nLi Ming"},

    {"id":"E-S-02","type":"english_small","exam":"英语一","max":10,"target":9,"low":8,"high":9,
     "prompt":"一名国际学生要做关于中国古代科学家的课堂口头报告，来信向你征求建议。请回复，推荐一位科学家并说明可介绍的内容。约100词。",
     "answer":"Dear Jack,\n\nFor your oral report, I recommend Zhang Heng, an outstanding scientist of the Eastern Han Dynasty. He made notable contributions to astronomy and designed an early seismoscope that indicated the direction of a distant earthquake.\n\nYou could organize the report in three parts: briefly introduce his historical background, explain how the seismoscope worked, and discuss why his achievements remain significant. A simple diagram of the device would help your classmates understand the mechanism, while a short comparison with modern instruments could make the presentation more engaging. Avoid including too many dates; focus instead on his scientific curiosity and practical creativity.\n\nI hope these suggestions are useful, and I look forward to hearing about your presentation.\n\nYours sincerely,\nLi Ming"},

    {"id":"E-S-03","type":"english_small","exam":"英语一","max":10,"target":7,"low":6,"high":8,
     "prompt":"为一位教授关于校园体育活动的研究项目写一则招募学生助手的通知，说明工作职责和申请要求。约100词。",
     "answer":"NOTICE\n\nA student assistant is needed for Professor Smith's research project on campus sports activities. The assistant will help collect questionnaires, interview students and organize the information gathered. He or she may also be asked to enter data into a computer.\n\nApplicants should be responsible, patient and interested in sports research. Basic computer skills and good communication ability are preferred. Students who can work for at least four hours each week are welcome to apply.\n\nPlease send a short introduction, your available time and contact information to sportsproject@university.edu before Friday.\n\nStudent Union"},

    {"id":"E-S-04","type":"english_small","exam":"英语一","max":10,"target":6,"low":5,"high":7,
     "prompt":"你和朋友Jack将调查一座古镇中老房屋的保护情况。给Jack写邮件，提出调查计划，包括调查对象、方法或分工。约100词。",
     "answer":"Dear Jack,\n\nI have made a simple plan for our survey on the protection of old houses in the ancient town. We can visit the town next Saturday and first take photos of several typical houses. Then we may interview local residents and ask them about the changes of these buildings.\n\nI suggest that you prepare the interview questions, while I contact the local community office and record the information. After the visit, we can put the photos and answers together and write a short report. Please tell me whether the time is convenient for you.\n\nBest wishes,\nLi Ming"},

    # === 政治分析题 ===
    {"id":"P-01","type":"politics","max":10,"target":4,"low":3,"high":5,
     "question":"材料围绕全党大兴调查研究。\n1. 如何理解调查能够掌握情况，却不会自然产生科学观点和正确结论？（5分）\n2. 为什么解决一个问题能够推动解决一类问题？（5分）",
     "materials":"材料强调调查要全面、客观、准确，研究要对材料进行分析整合，并从一个具体问题中发现更深层规律，推动解决一类问题。",
     "answer":"（1）实践是认识的来源，调查能够让人了解真实情况。但是调查以后还要认真思考，不能只看表面现象，要从材料中找到本质和规律，才能得到正确结论。\n\n（2）不同问题之间有共同的地方。解决一个问题以后，可以把经验用在其他问题上。因此我们要重视调查研究，从实际出发解决问题。",
     "scoring":"第（1）问：1.调查实践能够获得客观情况和感性材料。2.感性认识不能自动成为正确的理性认识。3.必须分析、综合、抽象和概括，实现感性认识向理性认识的飞跃。4.形成的认识还要回到实践接受检验并指导实践。\n第（2）问：1.矛盾普遍性与特殊性相互联结。2.具体问题具有特殊性，必须具体问题具体分析。3.个性中包含共性，典型问题能够反映同类问题的一般规律。4.从个别经验中概括一般认识，再用于指导其他同类问题。"},

    {"id":"P-02","type":"politics","max":10,"target":7,"low":6,"high":8,
     "question":"材料围绕全党大兴调查研究。\n1. 如何理解调查能够掌握情况，却不会自然产生科学观点和正确结论？（5分）\n2. 为什么解决一个问题能够推动解决一类问题？（5分）",
     "materials":"材料强调调查要全面、客观、准确，研究要对材料进行分析整合，并从一个具体问题中发现更深层规律，推动解决一类问题。",
     "answer":"（1）实践是认识的来源。调查作为实践活动，可以使人获得客观情况和感性材料，但感性材料只是认识的初级阶段，不会自动形成科学结论。还必须发挥理性思维的作用，对材料进行去粗取精、去伪存真、由此及彼、由表及里的加工，实现从感性认识到理性认识的飞跃。形成的观点还需要接受实践检验，并用于解决实际问题。\n\n（2）矛盾的普遍性和特殊性相互联结。每一个具体问题都有自身特点，必须具体问题具体分析；同时，同一类问题又具有共同性质。通过深入分析一个典型问题，可以从个性中概括共性、总结一般规律，再用这些经验指导其他相似问题，从而由点及面推动一类问题的解决。",
     "scoring":"第（1）问：1.调查实践能够获得客观情况和感性材料。2.感性认识不能自动成为正确的理性认识。3.必须分析、综合、抽象和概括，实现感性认识向理性认识的飞跃。4.形成的认识还要回到实践接受检验并指导实践。\n第（2）问：1.矛盾普遍性与特殊性相互联结。2.具体问题具有特殊性，必须具体问题具体分析。3.个性中包含共性，典型问题能够反映同类问题的一般规律。4.从个别经验中概括一般认识，再用于指导其他同类问题。"},

    {"id":"P-03","type":"politics","max":10,"target":9,"low":8,"high":10,
     "question":"材料围绕全党大兴调查研究。\n1. 如何理解调查能够掌握情况，却不会自然产生科学观点和正确结论？（5分）\n2. 为什么解决一个问题能够推动解决一类问题？（5分）",
     "materials":"材料强调调查要全面、客观、准确，研究要对材料进行分析整合，并从一个具体问题中发现更深层规律，推动解决一类问题。",
     "answer":"（1）调查属于社会实践，是获得客观情况和感性材料的重要途径，但材料的积累不等于科学认识的形成。感性认识反映的是事物的现象和外部联系，必须在调查基础上进行研究，运用分析与综合、抽象与概括等思维方法，对材料去粗取精、去伪存真、由此及彼、由表及里，完成由感性认识向理性认识的飞跃。理性结论还要回到实践中接受检验，并转化为解决群众实际问题的措施。因此，调查与研究不能割裂。\n\n（2）矛盾的普遍性寓于特殊性之中，并通过特殊性表现出来。具体问题具有不同条件和特点，必须坚持具体问题具体分析；但同类问题又包含共同矛盾和一般规律。通过对具有代表性的具体问题进行深入研究，可以从个性中把握共性，形成可推广的认识和方法，再结合其他地区、对象的具体条件加以运用。这样既避免简单照搬，又能够以点带面，推动一类问题得到解决。",
     "scoring":"第（1）问：1.调查实践能够获得客观情况和感性材料。2.感性认识不能自动成为正确的理性认识。3.必须分析、综合、抽象和概括，实现感性认识向理性认识的飞跃。4.形成的认识还要回到实践接受检验并指导实践。\n第（2）问：1.矛盾普遍性与特殊性相互联结。2.具体问题具有特殊性，必须具体问题具体分析。3.个性中包含共性，典型问题能够反映同类问题的一般规律。4.从个别经验中概括一般认识，再用于指导其他同类问题。"},

    {"id":"P-04","type":"politics","max":10,"target":5,"low":4,"high":6,
     "question":"材料讨论世界不稳定性、不确定性增强。\n1. 分析\"危机中育新机、变局中开新局\"所体现的唯物辩证法原理。（5分）\n2. 运用主观能动性与客观规律性相统一的原理，说明\"主动求变\"与\"准确识变\"的关系。（5分）",
     "materials":"材料提出要在危机中育新机、于变局中开新局，准确识变、科学应变、主动求变。",
     "answer":"（1）事物是不断发展变化的，危机中也可能出现新的机会。矛盾双方不是完全分开的，在一定条件下可以相互转化。因此面对危机不能只看到困难，也要看到有利条件，通过努力把危机变成机会。\n\n（2）规律是客观的，人应该尊重规律。同时，人也具有主观能动性，可以主动采取措施。准确识变就是看清实际情况，主动求变就是发挥人的作用。二者要结合起来，不能消极等待，也不能不顾实际盲目行动。",
     "scoring":"第（1）问：1.世界处于普遍联系和永恒发展之中，应以联系、发展、全面的观点看问题。2.矛盾双方既对立又统一，在一定条件下可以相互转化。3.危与机相伴而生，人的实践能够创造条件促成有利转化。\n第（2）问：1.尊重客观规律是正确发挥主观能动性的前提。2.发挥主观能动性有助于认识、利用规律并创造条件。3.实践是二者统一的基础。4.准确识变体现尊重客观实际，主动求变是在此基础上的积极实践。"},

    {"id":"P-05","type":"politics","max":10,"target":8,"low":7,"high":9,
     "question":"材料讨论世界不稳定性、不确定性增强。\n1. 分析\"危机中育新机、变局中开新局\"所体现的唯物辩证法原理。（5分）\n2. 运用主观能动性与客观规律性相统一的原理，说明\"主动求变\"与\"准确识变\"的关系。（5分）",
     "materials":"材料提出要在危机中育新机、于变局中开新局，准确识变、科学应变、主动求变。",
     "answer":"（1）唯物辩证法要求用联系、发展和全面的观点认识事物。危机与机遇是矛盾的两个方面，二者既相互区别又相互联系，并在一定条件下相互转化。危机包含破坏性，但也可能暴露旧有问题、催生新的需求和发展条件。人们通过正确认识形势并积极实践，可以创造条件，促使矛盾向有利方面转化，从而在危机中形成新机、在变局中开辟新局。\n\n（2）尊重客观规律是正确发挥主观能动性的前提，充分发挥主观能动性又是认识和利用规律的必要条件，实践是二者统一的基础。准确识变要求从客观实际出发，认识发展阶段、环境和条件的变化；主动求变则要求在把握规律的基础上积极行动、创造条件。只识变而不行动会陷入消极被动，只强调求变而不尊重规律则会导致主观主义。",
     "scoring":"第（1）问：1.世界处于普遍联系和永恒发展之中，应以联系、发展、全面的观点看问题。2.矛盾双方既对立又统一，在一定条件下可以相互转化。3.危与机相伴而生，人的实践能够创造条件促成有利转化。\n第（2）问：1.尊重客观规律是正确发挥主观能动性的前提。2.发挥主观能动性有助于认识、利用规律并创造条件。3.实践是二者统一的基础。4.准确识变体现尊重客观实际，主动求变是在此基础上的积极实践。"},
]


def run_test(tc, grader):
    """运行单个测试并返回分数"""
    tt = tc["type"]
    try:
        if tt == "english_big":
            r = grader.grade_big(
                student_answer=tc["answer"], prompt=tc["prompt"],
                exam_type=tc["exam"], max_score=tc["max"])
        elif tt == "english_small":
            r = grader.grade_small(
                student_answer=tc["answer"], prompt=tc["prompt"],
                exam_type=tc["exam"], max_score=tc["max"])
        else:
            r = grader.grade_single(
                student_answer=tc["answer"], question=tc["question"],
                materials=tc["materials"], max_score=tc["max"],
                subject_hint="马原",
                reference_scoring_points=tc.get("scoring",""))
        return r
    except Exception as e:
        return {"error": str(e)}


def main():
    eg = EnglishGrader()
    pg = PoliticsGrader()
    all_results = {}
    stats = defaultdict(list)

    print(f"Regression Test — {datetime.now().strftime('%H:%M:%S')}")
    print(f"Samples: {len(TESTS)} | 3 runs each\n")

    for tc in TESTS:
        tid = tc["id"]
        grader = pg if tc["type"] == "politics" else eg
        scores = []
        errors = []

        for run in range(3):
            r = run_test(tc, grader)
            if "error" in r:
                errors.append(r["error"])
                scores.append(None)
            else:
                scores.append(r.get("score", None))
            time.sleep(0.3)  # 避免速率限制

        # 判定
        valid = [s for s in scores if s is not None]
        if valid:
            avg = sum(valid) / len(valid)
            mn, mx = min(valid), max(valid)
            span = mx - mn
            passed = tc["low"] <= round(avg) <= tc["high"]
            status = "PASS" if passed else "FAIL"
        else:
            avg = mn = mx = span = None
            status = "ERR"

        print(f"[{status}] {tid} | target={tc['target']} [{tc['low']}-{tc['high']}] | "
              f"scores={scores} | avg={avg and round(avg,1)} | span={span} "
              f"{'| ALL_ERRORS' if errors else ''}")

        all_results[tid] = {"scores": scores, "avg": avg, "span": span,
                            "passed": passed if valid else False,
                            "errors": errors, "target": tc["target"],
                            "range": [tc["low"], tc["high"]]}

        if valid:
            stats["all_scores"].extend(valid)
            stats["pass"].append(1 if passed else 0)

    # Summary
    print(f"\n{'='*50}")
    passed = sum(stats["pass"])
    total = len([t for t in TESTS if all_results[t["id"]]["scores"][0] is not None])
    total_all = len(TESTS)
    if total:
        print(f"Pass: {passed}/{total} ({passed/total*100:.0f}%)")
    else:
        print("All samples failed with errors")
    if total < total_all:
        print(f"Error samples: {total_all - total}")

    if stats["all_scores"]:
        import statistics
        maes = [abs(s - all_results[tid]["target"]) for tid in all_results
                if all_results[tid]["avg"] is not None
                for s in all_results[tid]["scores"] if s is not None]
        print(f"MAE: {statistics.mean(maes):.2f} | 平均波动: {statistics.mean([all_results[tid]['span'] for tid in all_results if all_results[tid]['span'] is not None]):.2f}")

    # 保存完整结果
    out = {
        "time": datetime.now().isoformat(),
        "model": os.environ.get("LLM_MODEL", "?"),
        "results": {tid: {"scores": v["scores"], "avg": v["avg"],
                          "span": v["span"], "passed": v["passed"],
                          "errors": v["errors"]}
                    for tid, v in all_results.items()}
    }
    Path("test/results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n完整结果: test/results.json")


if __name__ == "__main__":
    main()
