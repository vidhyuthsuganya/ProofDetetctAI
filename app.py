import re
import ast
import operator
import streamlit as st

st.set_page_config(page_title="ProofDetect AI", page_icon="📐", layout="centered")

RULES = {
    "triangle": {
        "title": "Triangle angle-sum property",
        "rule": "The three interior angles of a triangle add up to 180°.",
        "why": "The interior angles of every triangle together form a straight angle of 180°.",
        "example": "If two angles are 50° and 60°, the third is 180° − 50° − 60° = 70°."
    },
    "straight": {
        "title": "Angles on a straight line",
        "rule": "Adjacent angles on a straight line add up to 180°.",
        "why": "A straight angle measures 180°. The parts into which it is divided must therefore total 180°.",
        "example": "If one angle is 125°, the adjacent angle is 180° − 125° = 55°."
    },
    "point": {
        "title": "Angles around a point",
        "rule": "Angles around a point add up to 360°.",
        "why": "A complete turn around a point is 360°.",
        "example": "If two angles are 90° and 120°, the remaining angle is 360° − 90° − 120° = 150°."
    },
    "vertical": {
        "title": "Vertically opposite angles",
        "rule": "Vertically opposite angles are equal when two straight lines intersect.",
        "why": "Each of the opposite angles is supplementary to the same adjacent angle, so they are equal.",
        "example": "If one angle is 65°, the angle directly opposite it is also 65°."
    },
    "isosceles": {
        "title": "Base angles of an isosceles triangle",
        "rule": "If two sides of a triangle are equal, the angles opposite those sides are equal.",
        "why": "Equal sides in an isosceles triangle have equal opposite angles.",
        "example": "If AB = AC, then angle ABC = angle BCA."
    },
    "pythagoras": {
        "title": "Pythagoras' theorem",
        "rule": "In a right-angled triangle, hypotenuse² = perpendicular² + base².",
        "why": "The square of the longest side is equal to the sum of the squares of the other two sides.",
        "example": "If the shorter sides are 3 and 4, the hypotenuse is √(3² + 4²) = 5."
    }
}

def nums(text):
    return [float(x) for x in re.findall(r'(?<![A-Za-z])\d+(?:\.\d+)?', text)]

def fmt(n):
    return str(int(n)) if abs(n-round(n)) < 1e-9 else f"{n:g}"

def solve_question(q):
    s = q.lower().replace("°", " degrees ")
    values = nums(s)

    # Triangle: many natural-language formulations
    triangle_words = any(w in s for w in ["triangle", "three angles", "third angle", "remaining angle", "last angle"])
    asks_missing = any(w in s for w in ["find", "calculate", "work out", "what is", "measure", "remaining", "third", "last"])
    if triangle_words and asks_missing and len(values) >= 2 and not any(w in s for w in ["right angle", "hypotenuse"]):
        a, b = values[0], values[1]
        ans = 180 - a - b
        if 0 < ans < 180:
            return ("SOLVED", f"The missing angle is **{fmt(ans)}°**.",
                    f"1. The angles inside a triangle add up to 180°.\n2. Add the known angles: {fmt(a)}° + {fmt(b)}° = {fmt(a+b)}°.\n3. Subtract from 180°: 180° − {fmt(a+b)}° = **{fmt(ans)}°**.",
                    RULES["triangle"])

    # Straight-line angles
    straight_words = any(w in s for w in ["straight line", "linear pair", "supplementary", "form a straight"])
    if straight_words and asks_missing and values:
        a = values[0]; ans = 180-a
        if 0 <= ans <= 180:
            return ("SOLVED", f"The missing angle is **{fmt(ans)}°**.",
                    f"Angles on a straight line total 180°.\n180° − {fmt(a)}° = **{fmt(ans)}°**.",
                    RULES["straight"])

    # Angles around a point
    point_words = any(w in s for w in ["around a point", "around the point", "complete turn", "full turn"])
    if point_words and asks_missing and values:
        total = sum(values); ans = 360-total
        if 0 <= ans <= 360:
            return ("SOLVED", f"The missing angle is **{fmt(ans)}°**.",
                    f"Angles around a point total 360°.\nKnown angles: {' + '.join(fmt(x)+'°' for x in values)} = {fmt(total)}°.\n360° − {fmt(total)}° = **{fmt(ans)}°**.",
                    RULES["point"])

    # Vertically opposite angles
    if "vertically opposite" in s and values and asks_missing:
        return ("SOLVED", f"The opposite angle is **{fmt(values[0])}°**.",
                "Vertically opposite angles are equal, so the opposite angle has the same measure.",
                RULES["vertical"])

    # Pythagoras, only when two shorter side lengths are clearly supplied
    if any(w in s for w in ["pythagoras", "hypotenuse"]) and len(values) >= 2:
        a, b = values[0], values[1]
        ans = (a*a+b*b)**0.5
        return ("SOLVED", f"The hypotenuse is **{fmt(ans)}**.",
                f"Using c² = a² + b²:\nc² = {fmt(a)}² + {fmt(b)}² = {fmt(a*a+b*b)}.\nc = √{fmt(a*a+b*b)} = **{fmt(ans)}**.",
                RULES["pythagoras"])

    # Simple arithmetic expression/equality, safely evaluated
    expr = q.strip().replace("^", "**")
    if re.fullmatch(r"[0-9+\-*/().\s]+", expr):
        try:
            tree = ast.parse(expr, mode="eval")
            allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd)
            if all(isinstance(n, allowed) for n in ast.walk(tree)):
                value = eval(compile(tree, "<math>", "eval"), {"__builtins__": {}}, {})
                return ("SOLVED", f"Answer: **{fmt(float(value))}**.", "The expression was evaluated using the indicated arithmetic operations.", None)
        except Exception:
            pass

    return ("NEEDS MORE DETAIL",
            "I couldn't confidently recognise this question yet.",
            "Try including the topic and the information given. For example: “A triangle has angles 50° and 60°. Find the remaining angle.”",
            None)

def identify_rule(text):
    s = text.lower()
    checks = [
        (["triangle", "180"], "triangle"),
        (["straight line", "180"], "straight"),
        (["around a point", "360"], "point"),
        (["vertically opposite"], "vertical"),
        (["isosceles", "equal sides", "ab = ac"], "isosceles"),
        (["pythagoras", "hypotenuse"], "pythagoras")
    ]
    for keys, key in checks:
        if any(k in s for k in keys):
            return RULES[key]
    return None

def check_step(given, claim, reason):
    text = (given + " " + claim + " " + reason).lower()
    r = reason.lower()
    if "vertically opposite" in r and ("intersect" in text or "two lines" in text):
        return "SUPPORTED PATTERN", "This may be valid if the two lines intersect and the angles are directly opposite. Check the diagram and angle labels."
    if "straight line" in r and nums(claim) and nums(claim)[0] <= 180:
        return "SUPPORTED PATTERN", "Angles on a straight line add to 180°. Confirm that the angles are adjacent and lie on the same straight line."
    if "triangle" in r and "180" in r:
        return "SUPPORTED PATTERN", "The triangle angle-sum property says its three interior angles total 180°. Confirm that the angles are interior angles of the same triangle."
    if "equal" in claim.lower() and ("parallel" in claim.lower() or "parallel" in r) and "length" in text:
        return "LIKELY INCORRECT", "Equal lengths alone do not prove that two lines are parallel. You need a suitable angle relationship or another valid parallel-line condition."
    if not reason.strip():
        return "NEEDS REVIEW", "Please provide the theorem, property, or reason used for this step."
    return "NEEDS REVIEW", "This prototype does not have enough information to verify this step reliably. Check the diagram, givens, and theorem with your teacher."

st.title("📐 ProofDetect AI")
st.caption("A free, rule-based mathematics proof checker and learning assistant")

st.info("This prototype recognises several common ways of asking supported questions. It does not understand every possible mathematical question or verify every proof.")

grade = st.selectbox("Choose your grade range", ["Grades 1–2", "Grades 3–5", "Grades 6–8", "Grades 9–10", "Grades 11–12", "Explore any level"])
topic = st.selectbox("Choose a topic", ["General mathematics", "Geometry and angles", "Triangles", "Algebra", "Pythagoras"])
mode = st.radio("What would you like to do?", ["Solve / explain a question", "Check a proof step", "Learn a mathematical rule", "Try an example"], horizontal=False)

if mode == "Solve / explain a question":
    st.subheader("Solve and explain")
    q = st.text_area("Type your mathematical question", placeholder="Example: A triangle has angles 50° and 60°. Find the third angle.")
    if st.button("Solve question", type="primary"):
        if q.strip():
            status, answer, explanation, rule = solve_question(q)
            st.markdown(f"### {status}")
            st.markdown(answer)
            st.markdown(explanation)
            if rule:
                with st.expander("Mathematical rule used"):
                    st.write(rule["title"])
                    st.write(rule["rule"])
                    st.write(rule["why"])
        else:
            st.warning("Please type a question first.")

elif mode == "Check a proof step":
    st.subheader("Check a proof step")
    given = st.text_area("Given information", placeholder="Example: AB = AC")
    claim = st.text_input("Your proof step / claim", placeholder="Example: angle ABC = angle BCA")
    reason = st.text_input("Reason used", placeholder="Example: Base angles of an isosceles triangle are equal")
    if st.button("Check step", type="primary"):
        status, explanation = check_step(given, claim, reason)
        st.markdown(f"### {status}")
        st.write(explanation)

elif mode == "Learn a mathematical rule":
    st.subheader("Learn a rule")
    choice = st.selectbox("Select a rule", list(RULES.keys()), format_func=lambda k: RULES[k]["title"])
    rule = RULES[choice]
    st.markdown(f"**Rule:** {rule['rule']}")
    st.write(f"**Why it works:** {rule['why']}")
    st.write(f"**Example:** {rule['example']}")

else:
    st.subheader("Try an example")
    examples = {
        "Triangle angle sum": "A triangle has angles 50° and 60°. Find the third angle.",
        "Straight line": "An angle of 125° and x form a straight line. Find x.",
        "Angles around a point": "Angles around a point are 90°, 120° and x. Find x.",
        "Vertically opposite": "One of a pair of vertically opposite angles is 65°. Find the other angle.",
        "Pythagoras": "Using Pythagoras, find the hypotenuse when the other sides are 3 and 4."
    }
    sample = st.selectbox("Choose a sample", list(examples.keys()))
    st.code(examples[sample])
    if st.button("Run sample", type="primary"):
        status, answer, explanation, rule = solve_question(examples[sample])
        st.markdown(f"### {status}")
        st.markdown(answer)
        st.markdown(explanation)
        if rule:
            st.caption(f"Rule used: {rule['title']}")

st.divider()
st.caption("ProofDetect AI is an educational prototype. Always verify important proof steps and answers with a teacher or trusted textbook.")
