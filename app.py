import re
import math
import ast
import streamlit as st
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr, standard_transformations, implicit_multiplication_application,
    convert_xor, rationalize
)

st.set_page_config(page_title="ProofDetect AI", page_icon="📐", layout="centered")

x, y, z = sp.symbols("x y z")
TRANSFORMS = standard_transformations + (
    implicit_multiplication_application, convert_xor, rationalize
)

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

def fmt(value):
    try:
        value = sp.simplify(value)
        if value.is_Integer:
            return str(value)
        if value.is_Rational:
            return str(value)
        return sp.sstr(value)
    except Exception:
        return str(value)

def safe_parse(raw):
    """Parse a maths expression using SymPy, with implicit multiplication (2x, 3(x+1))."""
    raw = raw.strip().replace("−", "-").replace("×", "*").replace("÷", "/")
    raw = raw.replace("^", "**")
    if not raw or len(raw) > 250:
        raise ValueError("Please enter a shorter mathematical expression.")
    if not re.fullmatch(r"[0-9a-zA-Z_+\-*/().,\s\[\]]+", raw):
        raise ValueError("Please use standard maths symbols and variables such as x, +, −, ×, ÷, brackets and powers.")
    return parse_expr(
        raw, local_dict={"x": x, "y": y, "z": z},
        transformations=TRANSFORMS, evaluate=True
    )

def extract_equation(question):
    q = question.lower().strip()
    q = q.replace("−", "-").replace("×", "*").replace("÷", "/")
    q = q.replace("equals to", "=").replace("is equal to", "=")
    q = q.replace("equal to", "=")
    # Remove common instruction words, but retain the equation itself.
    q = re.sub(r"\b(find|solve|calculate|work out|determine|what is|what's|please|the value of|for|x)\b(?=\s*=|$)", "", q)
    q = q.replace("?", "").strip()
    # A user may write "2x + 3 = 8, find x".
    matches = re.findall(r"([0-9a-zA-Z_+\-*/().\s^]+=[0-9a-zA-Z_+\-*/().\s^]+)", q)
    if matches:
        return matches[0].strip().rstrip(",.")
    # A plain equation with a trailing instruction.
    if "=" in q:
        left, right = q.split("=", 1)
        right = re.split(r",|\bfind\b|\bsolve\b", right)[0]
        return left.strip() + "=" + right.strip()
    return None

def solve_algebra(question):
    equation_text = extract_equation(question)
    if equation_text:
        left_text, right_text = equation_text.split("=", 1)
        lhs, rhs = safe_parse(left_text), safe_parse(right_text)
        equation = sp.Eq(lhs, rhs)
        symbols = sorted(equation.free_symbols, key=lambda s: s.name)
        if not symbols:
            return ("SOLVED", f"**{fmt(sp.simplify(lhs-rhs)) == '0'}**",
                    f"Compare both sides: left side = {fmt(lhs)} and right side = {fmt(rhs)}.", None)
        target = x if x in symbols else symbols[0]
        solutions = sp.solve(equation, target)
        if not solutions:
            return ("NO SOLUTION FOUND", "I couldn't find a solution for this equation.", "Check that the equation was typed correctly.", None)
        steps = [
            f"1. Start with: **{sp.sstr(lhs)} = {sp.sstr(rhs)}**",
            f"2. Bring everything to one side: **{sp.sstr(sp.expand(lhs-rhs))} = 0**",
            f"3. Solve for **{target}**."
        ]
        if len(solutions) == 1:
            steps.append(f"4. Therefore, **{target} = {fmt(solutions[0])}**.")
        else:
            steps.append(f"4. The solutions are **{target} = {', '.join(fmt(v) for v in solutions)}**.")
        return ("SOLVED", f"**Solution: {target} = {', '.join(fmt(v) for v in solutions)}**",
                "\n\n".join(steps) + "\n\nThe equation is solved using symbolic algebra.", None)

    # Algebraic expression actions.
    q = question.strip()
    action = "simplify"
    if re.search(r"\b(expand|multiply out)\b", q, re.I):
        action = "expand"
    elif re.search(r"\b(factor|factorise|factorize)\b", q, re.I):
        action = "factor"
    elif re.search(r"\b(simplify|reduce)\b", q, re.I):
        action = "simplify"
    else:
        return None
    expression = re.sub(r"\b(expand|multiply out|factorise|factorize|factor|simplify|reduce|the expression|expression)\b", "", q, flags=re.I).strip(" :?")
    expr = safe_parse(expression)
    result = {"expand": sp.expand, "factor": sp.factor, "simplify": sp.simplify}[action](expr)
    label = {"expand": "Expanded form", "factor": "Factorised form", "simplify": "Simplified form"}[action]
    return ("SOLVED", f"**{label}: {sp.sstr(result)}**",
            f"Starting expression: **{sp.sstr(expr)}**\n\nAfter {action}ing: **{sp.sstr(result)}**", None)

def solve_question(q):
    s = q.lower().replace("°", " degrees ")
    values = [float(v) for v in re.findall(r"(?<![a-z])\d+(?:\.\d+)?", s)]

    # Algebra first, so equations are not mistaken for geometry numbers.
    try:
        algebra = solve_algebra(q)
        if algebra:
            return algebra
    except Exception as e:
        if "=" in q or any(k in s for k in ["factor", "expand", "simplify"]):
            return ("NEEDS MORE DETAIL", "I recognised a maths expression, but couldn't parse it safely.",
                    "Check brackets, operators and variable names. Example: 2x + 3 = 6 + x, find x.", None)

    triangle_words = any(w in s for w in ["triangle", "three angles", "third angle", "remaining angle", "last angle"])
    asks_missing = any(w in s for w in ["find", "calculate", "work out", "what is", "measure", "remaining", "third", "last"])
    if triangle_words and asks_missing and len(values) >= 2 and not any(w in s for w in ["right angle", "hypotenuse"]):
        a, b = values[0], values[1]
        ans = 180 - a - b
        if 0 < ans < 180:
            return ("SOLVED", f"The missing angle is **{fmt(ans)}°**.",
                    f"1. The angles inside a triangle add up to 180°.\n2. Add the known angles: {fmt(a)}° + {fmt(b)}° = {fmt(a+b)}°.\n3. Subtract from 180°: 180° − {fmt(a+b)}° = **{fmt(ans)}°**.",
                    RULES["triangle"])

    if any(w in s for w in ["straight line", "linear pair", "supplementary", "form a straight"]) and asks_missing and values:
        a = values[0]; ans = 180-a
        if 0 <= ans <= 180:
            return ("SOLVED", f"The missing angle is **{fmt(ans)}°**.",
                    f"Angles on a straight line total 180°.\n180° − {fmt(a)}° = **{fmt(ans)}°**.", RULES["straight"])

    if any(w in s for w in ["around a point", "around the point", "complete turn", "full turn"]) and asks_missing and values:
        total = sum(values); ans = 360-total
        if 0 <= ans <= 360:
            return ("SOLVED", f"The missing angle is **{fmt(ans)}°**.",
                    f"Angles around a point total 360°.\nKnown angles total {fmt(total)}°.\n360° − {fmt(total)}° = **{fmt(ans)}°**.", RULES["point"])

    if "vertically opposite" in s and values and asks_missing:
        return ("SOLVED", f"The opposite angle is **{fmt(values[0])}°**.",
                "Vertically opposite angles are equal, so the opposite angle has the same measure.", RULES["vertical"])

    if any(w in s for w in ["pythagoras", "hypotenuse"]) and len(values) >= 2:
        a, b = values[0], values[1]
        ans = sp.sqrt(a*a+b*b)
        return ("SOLVED", f"The hypotenuse is **{fmt(ans)}**.",
                f"Using c² = a² + b²:\nc² = {fmt(a)}² + {fmt(b)}² = {fmt(a*a+b*b)}.\nc = **{fmt(ans)}**.", RULES["pythagoras"])

    # Arithmetic-only expressions, including "what is 3*(4+2)".
    candidate = re.sub(r"^(what is|calculate|evaluate|work out|solve)\s+", "", q, flags=re.I).strip(" ?")
    if re.fullmatch(r"[0-9+\-*/().\s^]+", candidate):
        try:
            expr = safe_parse(candidate)
            result = sp.simplify(expr)
            return ("SOLVED", f"**Answer: {fmt(result)}**",
                    f"Evaluated expression: **{sp.sstr(expr)} = {fmt(result)}**", None)
        except Exception:
            pass

    return ("NEEDS MORE DETAIL",
            "I couldn't confidently recognise this question yet.",
            "This version supports common algebraic equations, expressions, arithmetic and selected geometry topics. Try: **2x + 3 = 6 + x, find x**.", None)

def identify_rule(text):
    s = text.lower()
    checks = [
        (["triangle", "180"], "triangle"), (["straight line", "180"], "straight"),
        (["around a point", "360"], "point"), (["vertically opposite"], "vertical"),
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
    if "straight line" in r and re.search(r"\d", claim):
        return "SUPPORTED PATTERN", "Angles on a straight line add to 180°. Confirm that the angles are adjacent and lie on the same straight line."
    if "triangle" in r and "180" in r:
        return "SUPPORTED PATTERN", "The triangle angle-sum property says its three interior angles total 180°. Confirm that the angles are interior angles of the same triangle."
    if "equal" in claim.lower() and ("parallel" in claim.lower() or "parallel" in r) and "length" in text:
        return "LIKELY INCORRECT", "Equal lengths alone do not prove that two lines are parallel. You need a suitable angle relationship or another valid parallel-line condition."
    if not reason.strip():
        return "NEEDS REVIEW", "Please provide the theorem, property, or reason used for this step."
    return "NEEDS REVIEW", "This prototype cannot fully verify this proof step yet. Check the diagram, givens, and theorem. 'Needs review' does not mean the step is wrong."

st.title("📐 ProofDetect AI")
st.caption("A free mathematics tutor and proof-checking learning assistant")

st.info("ProofDetect AI is an evolving educational prototype. It can solve supported algebra, arithmetic and geometry questions, but it does not yet understand every possible question or independently verify every proof.")

grade = st.selectbox("Choose your grade range", ["Grades 1–2", "Grades 3–5", "Grades 6–8", "Grades 9–10", "Grades 11–12", "Explore any level"])
mode = st.radio("What would you like to do?", ["Solve / explain a question", "Check a proof step", "Learn a mathematical rule", "Try an example"])

if mode == "Solve / explain a question":
    st.subheader("Maths tutor")
    q = st.text_area("Type your mathematical question", placeholder="Try: 2x + 3 = 6 + x, find x")
    if st.button("Solve question", type="primary"):
        if q.strip():
            status, answer, explanation, rule = solve_question(q)
            st.markdown(f"### {status}")
            st.markdown(answer)
            st.markdown(explanation)
            if rule:
                with st.expander("Mathematical rule used"):
                    st.write(rule["title"]); st.write(rule["rule"]); st.write(rule["why"])
        else:
            st.warning("Please type a question first.")

elif mode == "Check a proof step":
    st.subheader("Proof checker")
    given = st.text_area("Given information", placeholder="Example: AB = AC")
    claim = st.text_input("Your proof step / claim", placeholder="Example: angle ABC = angle BCA")
    reason = st.text_input("Reason used", placeholder="Example: Base angles of an isosceles triangle are equal")
    if st.button("Check step", type="primary"):
        status, explanation = check_step(given, claim, reason)
        st.markdown(f"### {status}"); st.write(explanation)

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
        "Linear equation": "2x + 3 = 6 + x, find x",
        "Equation with brackets": "3(x + 2) = 15, solve",
        "Quadratic equation": "x^2 - 5x + 6 = 0, solve",
        "Simplify": "simplify 2x + 3x - 4",
        "Expand": "expand 3(x + 2)",
        "Factorise": "factorise x^2 + 5x + 6",
        "Triangle angle sum": "A triangle has angles 50° and 60°. Find the third angle.",
        "Straight line": "An angle of 125° and x form a straight line. Find x.",
        "Angles around a point": "Angles around a point are 90°, 120° and x. Find x.",
        "Pythagoras": "Using Pythagoras, find the hypotenuse when the other sides are 3 and 4."
    }
    sample = st.selectbox("Choose a sample", list(examples.keys()))
    st.code(examples[sample])
    if st.button("Run sample", type="primary"):
        status, answer, explanation, rule = solve_question(examples[sample])
        st.markdown(f"### {status}"); st.markdown(answer); st.markdown(explanation)
        if rule:
            st.caption(f"Rule used: {rule['title']}")

st.divider()
st.caption("ProofDetect AI is free to try. For important work, verify answers and proof steps with a teacher or trusted textbook.")
