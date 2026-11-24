"""Local token-to-option matching for development datasets."""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "final-evals"))
from lens_eval.data import clean_submission, read_questions
from lens_eval.scoring import layer_votes, plurality


WEEKDAYS = (
    "Monday Tuesday Wednesday Thursday Friday Saturday Sunday",
    "lunes martes miércoles jueves viernes sábado domingo",
    "lundi mardi mercredi jeudi vendredi samedi dimanche",
    "Montag Dienstag Mittwoch Donnerstag Freitag Samstag Sonntag",
    "понедельник вторник среда четверг пятница суббота воскресенье",
    "segunda-feira terça-feira quarta-feira quinta-feira sexta-feira sábado domingo",
    "星期一 星期二 星期三 星期四 星期五 星期六 星期日",
    "周一 周二 周三 周四 周五 周六 周日",
    "月曜日 火曜日 水曜日 木曜日 金曜日 土曜日 日曜日",
    "월요일 화요일 수요일 목요일 금요일 토요일 일요일",
    "सोमवार मंगलवार बुधवार गुरुवार शुक्रवार शनिवार रविवार",
    "الاثنين الثلاثاء الأربعاء الخميس الجمعة السبت الأحد",
    "จันทร์ อังคาร พุธ พฤหัสบดี ศุกร์ เสาร์ อาทิตย์",
)
MONTHS = (
    "January February March April May June July August September October November December",
    "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre",
    "janvier février mars avril mai juin juillet août septembre octobre novembre décembre",
    "Januar Februar März April Mai Juni Juli August September Oktober November Dezember",
    "январь февраль март апрель май июнь июль август сентябрь октябрь ноябрь декабрь",
    "января февраля марта апреля мая июня июля августа сентября октября ноября декабря",
    "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro",
    "gennaio febbraio marzo aprile maggio giugno luglio agosto settembre ottobre novembre dicembre",
    "一月 二月 三月 四月 五月 六月 七月 八月 九月 十月 十一月 十二月",
    "1月 2月 3月 4月 5月 6月 7月 8月 9月 10月 11月 12月",
    "1월 2월 3월 4월 5월 6월 7월 8월 9월 10월 11월 12월",
    "जनवरी फ़रवरी मार्च अप्रैल मई जून जुलाई अगस्त सितंबर अक्टूबर नवंबर दिसंबर",
    "يناير فبراير مارس أبريل مايو يونيو يوليو أغسطس سبتمبر أكتوبر نوفمبر ديسمبر",
    "มกราคม กุมภาพันธ์ มีนาคม เมษายน พฤษภาคม มิถุนายน กรกฎาคม สิงหาคม กันยายน ตุลาคม พฤศจิกายน ธันวาคม",
)


def normalize(text):
    text = unicodedata.normalize("NFKC", text).casefold().strip()
    if re.fullmatch(r"[+−-]?\d+(?:[.,]\d+)*", text):
        return text
    # Keep an attached sign or decimal point so a numeric fragment cannot name 7.
    start = 0
    while start < len(text) and (text[start].isspace() or unicodedata.category(text[start]).startswith("P")):
        if text[start] in "-.," and text[start + 1 : start + 2].isdecimal():
            break
        start += 1
    end = len(text)
    while end > start and (text[end - 1].isspace() or unicodedata.category(text[end - 1]).startswith("P")):
        end -= 1
    return text[start:end]


def number_names():
    english = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
    english_tens = "twenty thirty forty fifty sixty seventy eighty ninety".split()
    spanish = "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro veinticinco veintiséis veintisiete veintiocho veintinueve".split()
    spanish_tens = "treinta cuarenta cincuenta sesenta setenta ochenta noventa".split()
    chinese = "零一二三四五六七八九"
    for number in range(101):
        names = {str(number)}
        tens, units = divmod(number, 10)
        if number == 100:
            names.update(("one hundred", "a hundred", "cien", "一百", "百"))
        else:
            if number < 20:
                names.add(english[number])
            else:
                base = english_tens[tens - 2]
                names.update((f"{base}-{english[units]}", f"{base} {english[units]}") if units else (base,))
            if number < 30:
                names.add(spanish[number])
            else:
                base = spanish_tens[tens - 3]
                names.add(f"{base} y {spanish[units]}" if units else base)
            if number < 10:
                names.add(chinese[number])
            else:
                names.add((chinese[tens] if tens > 1 else "") + "十" + (chinese[units] if units else ""))
        yield number, names


def aliases():
    result = {}
    for category, languages in (("weekday", WEEKDAYS), ("month", MONTHS)):
        for language in languages:
            for index, name in enumerate(language.split()):
                result[normalize(name)] = (category, index)
    for number, names in number_names():
        for name in names:
            result[normalize(name)] = ("number", number)
    for language in (
        "zéro un deux trois quatre cinq six sept huit neuf dix onze douze treize quatorze quinze seize dix-sept dix-huit dix-neuf",
        "null eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf dreizehn vierzehn fünfzehn sechzehn siebzehn achtzehn neunzehn",
        "ноль один два три четыре пять шесть семь восемь девять десять одиннадцать двенадцать тринадцать четырнадцать пятнадцать шестнадцать семнадцать восемнадцать девятнадцать",
        "صفر واحد اثنان ثلاثة أربعة خمسة ستة سبعة ثمانية تسعة عشرة",
        "शून्य एक दो तीन चार पाँच छह सात आठ नौ दस",
        "영 일 이 삼 사 오 육 칠 팔 구 십",
        "ศูนย์ หนึ่ง สอง สาม สี่ ห้า หก เจ็ด แปด เก้า สิบ",
    ):
        for number, name in enumerate(language.split()):
            result[normalize(name)] = ("number", number)
    result.update({"星期天": ("weekday", 6), "周天": ("weekday", 6), "兩": ("number", 2), "两": ("number", 2)})
    return result


ALIASES = aliases()


def token_key(text):
    name = normalize(text)
    if re.fullmatch(r"[+−-]?\d+", name):
        return ("number", int(name.replace("−", "-")))
    if name in ALIASES:
        return ALIASES[name]
    if name.isascii() and name.isalpha() and len(name) > 3:
        if name.endswith("ies"):
            name = name[:-3] + "y"
        elif name.endswith(("ches", "shes", "sses", "xes", "zzes")):
            name = name[:-2]
        elif name.endswith("s") and not name.endswith(("ss", "us", "is", "as")):
            name = name[:-1]
    return ("word", name)


def score(questions, rows):
    by_id = {row["id"]: row for row in rows}
    for q in questions.values():
        cleaned, reason = clean_submission(by_id.get(q["id"]), questions)
        result = {"id": q["id"], "pass": False, "layer_votes": {}}
        if reason:
            yield {**result, "reason": reason}
            continue
        options = [token_key(option) for option in q["options"]]
        ranked = {}
        for readout in cleaned["readouts"]:
            ranks = {}
            for index, token in enumerate(readout["tokens"], start=1):
                key = token_key(token)
                for option, option_key in enumerate(options):
                    if key == option_key:
                        ranks.setdefault(option, index)
            ranked[readout["layer"]] = ranks
        votes = layer_votes({layer: ranks for layer, ranks in ranked.items() if ranks})
        yield {
            **result,
            "pass": plurality(votes, q["options"].index(q["intermediate"])),
            "layer_votes": {visit: q["options"][option] for visit, option in votes.items()},
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("questions", type=Path)
    parser.add_argument("readouts", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.readouts.read_text().split("\n") if line.strip()]
    results = list(score(read_questions(args.questions), rows))
    args.output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in results))
    print(f"Proxy passed {sum(row['pass'] for row in results)}/{len(results)}. Votes in {args.output}")


if __name__ == "__main__":
    main()
