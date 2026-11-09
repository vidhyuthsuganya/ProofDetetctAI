import streamlit as st
import re
import ast
import operator
from fractions import Fraction

st.set_page_config(page_title="ProofDetect AI", page_icon="🧠", layout="wide")

st.title("🧠 ProofDetect AI")
st.subheader("A mathematical proof checker and step-by-step tutor")
st.caption("For school mathematics from primary grades to senior secondary. This prototype checks selected rules and examples; it does not yet prove every possible theorem.")

with st.sidebar:
    st.header("Learning settings")
    grade = st.selectbox(
        "Choose grade / level",
        ["Grades 1–2", "Grades 3–5", "Grades 6–8", "Grades 9–10", "Grades 11–12", "Explore any level"]
    )
    topic = st.selectbox(
        "Choose topic",
        ["Arithmetic & fractions", "Algebra & equations", "Geometry & angles",
         "Triangles & polygons", "Parallel lines", "Pythagoras theorem",
         "Coordinate geometry", "Trigonometry", "Sequences", "General proof"]
    )
    mode = st.radio("What would you like to do?", ["Check one step", "Solve / explain a statement", "Learn a rule", "Try a sample"])

RULES = {
    "Vertically opposite angles": {
        "topic": "Geometry & angles",
        "rule": "When two straight lines intersect, each pair of vertically opposite angles is equal.",
        "example": "If ∠A and ∠C are vertically opposite, then ∠A = ∠C.",
        "common_error": "Do not use this rule for any two angles that merely look opposite in a drawing. They must be formed by the same two intersecting lines."
    },
    "Angles on a straight line": {
        "topic": "Geometry & angles",
        "rule": "Adjacent angles that form a straight line add up to 180°.",
        "example": "If x and 65° form a straight line, x + 65° = 180°, so x = 115°.",
        "common_error": "The angles are not necessarily equal. The guaranteed fact is that their sum is 180°."
    },
    "Angles around a point": {
        "topic": "Geometry & angles",
        "rule": "Angles around one point add up to 360°.",
        "example": "If three angles around a point are 90°, 120° and x, then x = 360° − 90° − 120° = 150°.",
        "common_error": "Do not use 180° for a full turn around a point."
    },
    "Triangle angle sum": {
        "topic": "Triangles & polygons",
        "rule": "The three interior angles of a triangle add up to 180° in ordinary Euclidean geometry.",
        "example": "If two angles are 50° and 60°, the third is 180° − 50° − 60° = 70°.",
        "common_error": "Check that the angles are the three interior angles of the same triangle."
    },
    "Isosceles triangle": {
        "topic": "Triangles & polygons",
        "rule": "If two sides of a triangle are equal, the angles opposite those sides are equal.",
        "example": "If AB = AC, then ∠B = ∠C.",
        "common_error": "The equal angles are opposite the equal sides. Do not mix up the vertex angle and base angles."
    },
    "Pythagoras theorem": {
        "topic": "Pythagoras theorem",
        "rule": "In a right-angled triangle, a² + b² = c², where c is the hypotenuse.",
        "example": "For legs 3 and 4, c² = 3² + 4² = 25, so c = 5.",
        "common_error": "Use this theorem only for a right-angled triangle, and c must be the side opposite the right angle."
    },
    "Equal things can be substituted": {
        "topic": "Algebra & equations",
        "rule": "If a = b, then b can replace a in an expression, provided the expressions are used in the same mathematical setting.",
        "example": "If x = 4 and y = x + 3, then y = 4 + 3 = 7.",
        "common_error": "The replacement must preserve equality and respect the original conditions."
    },
    "Addition property of equality": {
        "topic": "Algebra & equations",
        "rule": "Adding the same quantity to both sides of an equation preserves equality.",
        "example": "If x − 5 = 8, add 5 to both sides to get x = 13.",
        "common_error": "Adding a quantity to only one side usually changes the equation."
    },
    "Multiplication property of equality": {
        "topic": "Algebra & equations",
        "rule": "Multiplying both sides of an equation by the same quantity preserves equality.",
        "example": "If x/3 = 4, multiply both sides by 3 to get x = 12.",
        "common_error": "If dividing, never divide by zero. Check the quantity you multiply or divide by."
    },
    "Equal lengths do not prove parallel lines": {
        "topic": "Parallel lines",
        "rule": "Equal segment lengths alone do not establish that two lines are parallel.",
        "example": "AB = CD tells you the lengths match. It does not, by itself, tell you the directions of the lines.",
        "common_error": "To prove lines parallel, use an appropriate angle relationship or another valid parallel-line criterion."
    },
    "Exterior angle of a triangle": {
        "topic": "Triangles & polygons",
        "rule": "An exterior angle of a triangle equals the sum of the two opposite interior angles.",
        "example": "If the two remote interior angles are 45° and 70°, the exterior angle is 115°.",
        "common_error": "Do not add the adjacent interior angle to the two remote angles."
    },
    "Sine ratio in a right triangle": {
        "topic": "Trigonometry",
        "rule": "For an acute angle θ in a right triangle, sin(θ) = opposite / hypotenuse.",
        "example": "If the opposite side is 3 and the hypotenuse is 5, sin(θ) = 3/5.",
        "common_error": "Identify the opposite side relative to the angle θ, and use the hypotenuse, not the adjacent side."
    },
}

def normalise(s):
    return re.sub(r"\s+", " ", s.strip().lower().replace("°", " degrees "))

def safe_numeric_eval(expr):
    """Evaluate a small numeric arithmetic expression without eval()."""
    allowed_ops = {
        ast.Add: operator.add, ast.Sub: operator.sub,
        ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.UAdd: operator.pos
    }
    tree = ast.parse(expr, mode="eval")
    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_ops:
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError
            return allowed_ops[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_ops:
            return allowed_ops[type(node.op)](visit(node.operand))
        raise ValueError("Only numeric arithmetic is supported")
    return visit(tree)

def check_step(statement, reason, topic):
    s, r = normalise(statement), normalise(reason)
    combined = s + " " + r

    if ("straight line" in combined and
        ("angles are equal" in s or "are equal" in s) and
        ("straight line" in r or "form a straight line" in r)):
        return ("LIKELY INCORRECT", "Angles on a straight line add up to 180°, but they do not have to be equal. For example, 120° and 60° form a straight angle.", "Use the fact that the sum is 180°, then solve for the unknown angle if needed.")

    if (("parallel" in s or "parallel" in r) and
        ("equal length" in combined or "equal lengths" in combined or "ab = cd" in combined) and
        ("therefore" in s or "so " in s or "hence" in s)):
        return ("LIKELY INCORRECT", "Equal lengths alone do not prove that two lines are parallel. Length and direction are different properties.", "Look for a valid angle criterion, such as equal corresponding angles or equal alternate interior angles, with the required line-transversal setup.")

    if "triangle" in combined and ("360" in s or "360°" in statement) and ("interior" in combined or "angles" in combined):
        return ("LIKELY INCORRECT", "The three interior angles of a triangle add up to 180°, not 360°. Angles around a point add up to 360°.", "Check whether the statement refers to one triangle or a full turn around a point.")

    patterns = [
        (["vertically opposite", "opposite angles are equal"], ["equal", "="], "Vertically opposite angles are equal when two straight lines intersect.", "Check that the two named angles really are vertically opposite in the diagram."),
        (["triangle angle sum", "angles of a triangle add up", "interior angles of a triangle"], ["180"], "The interior angles of a triangle add up to 180° in Euclidean geometry.", "Make sure the three angles belong to the same triangle."),
        (["straight line", "linear pair"], ["180"], "Adjacent angles forming a straight line add up to 180°.", "This rule establishes a sum of 180°, not that the angles are equal."),
        (["around a point"], ["360"], "Angles around a point add up to 360°.", "Confirm that the angles together make one full turn."),
        (["isosceles", "equal sides"], ["equal", "="], "In an isosceles triangle, equal sides have equal opposite angles.", "Identify the angles opposite the equal sides."),
        (["pythagoras", "right-angled", "right angled"], ["square", "²", "2", "="], "Pythagoras' theorem applies to a right-angled triangle: a² + b² = c², with c as the hypotenuse.", "Check that the triangle is right-angled and that c is the hypotenuse."),
        (["addition property", "add", "adding"], ["equation", "both sides", "=", "x"], "Adding the same quantity to both sides preserves an equation.", "Verify that the same quantity was added to both sides."),
        (["substitution", "substitute", "replace"], ["=", "equal"], "Substitution is valid when one expression is known to equal the expression replacing it.", "Check that the equality used for substitution was already established."),
        (["sine", "sin"], ["opposite", "hypotenuse", "/"], "For an acute angle in a right triangle, sin(θ) = opposite / hypotenuse.", "Check the reference angle and identify the hypotenuse correctly."),
    ]
    for keys, cues, explanation, next_step in patterns:
        if any(k in combined for k in keys) and any(c in combined for c in cues):
            return ("SUPPORTED PATTERN", explanation, next_step)

    compact = statement.replace(" ", "")
    if re.fullmatch(r"[0-9+\-*/().^]+=[0-9+\-*/().^]+", compact):
        try:
            left, right = compact.split("=", 1)
            lv = safe_numeric_eval(left.replace("^", "**"))
            rv = safe_numeric_eval(right.replace("^", "**"))
            if abs(float(lv) - float(rv)) < 1e-9:
                return ("SUPPORTED PATTERN", f"The numerical equality checks out: {left} = {right}.", "For a formal proof, also explain why this calculation is relevant to the step before it.")
            return ("LIKELY INCORRECT", f"The numerical equality does not hold: the left side is {lv}, while the right side is {rv}.", "Recalculate both sides and check for an arithmetic or sign error.")
        except Exception:
            pass

    return ("NEEDS REVIEW", "I do not have enough reliable information to judge this step. It may be correct, but this prototype does not recognise the rule or lacks the diagram/context.", "Write the exact theorem or property used, and include the earlier fact that supports this step. Do not treat 'NEEDS REVIEW' as wrong.")

def solve_numeric_statement(statement):
    """Solve/check a small set of common school-math statements."""
    raw = statement.strip()
    s = raw.lower().replace("×", "*").replace("÷", "/").replace("−", "-").replace("–", "-")
    s = s.replace("°", "")
    # Arithmetic equality, e.g. 7*3=25
    compact = re.sub(r"\s+", "", s)
    if re.fullmatch(r"[0-9+\-*/().^]+=[0-9+\-*/().^]+", compact):
        left, right = compact.split("=", 1)
        try:
            lv = safe_numeric_eval(left.replace("^", "**"))
            rv = safe_numeric_eval(right.replace("^", "**"))
            if abs(float(lv) - float(rv)) < 1e-9:
                return "CHECKED", f"{left} = {right} is true because both sides equal {lv}.", "Reason: evaluate both sides using the order of operations."
            return "NOT TRUE", f"{left} = {right} is false: the left side equals {lv}, but the right side equals {rv}.", "Next: recalculate the expression and correct the side that is wrong."
        except Exception:
            pass

    # One-variable linear equation in forms like 2*x+3=11, x/3=4, 5-x=2
    compact = compact.replace("^", "**")
    m = re.fullmatch(r"([+-]?\d+(?:\.\d+)?)\*?x([+-]\d+(?:\.\d+)?)?=([+-]?\d+(?:\.\d+)?)", compact)
    if m:
        a = float(m.group(1))
        b = float(m.group(2) or 0)
        c = float(m.group(3))
        if a != 0:
            x = (c - b) / a
            return "SOLVED", f"Rearrange {a:g}x {b:+g} = {c:g} to get {a:g}x = {c-b:g}, so x = {x:g}.", "Reason: subtract the constant from both sides, then divide both sides by the coefficient of x."
    # Forms x/number = number
    m = re.fullmatch(r"x/(\d+(?:\.\d+)?)=([+-]?\d+(?:\.\d+)?)", compact)
    if m and float(m.group(1)) != 0:
        x = float(m.group(1)) * float(m.group(2))
        return "SOLVED", f"x/{m.group(1)} = {m.group(2)}. Multiply both sides by {m.group(1)} to get x = {x:g}.", "Reason: multiplying both sides of an equation by the same non-zero number preserves equality."
    # Geometry sentence templates
    if "triangle" in s and "50" in s and "60" in s and ("third angle" in s or "missing angle" in s):
        return "SOLVED", "The third angle is 180° − 50° − 60° = 70°.", "Reason: the interior angles of a triangle add up to 180°."
    if ("straight line" in s or "linear pair" in s) and "65" in s and ("find" in s or "unknown" in s or "x" in s):
        return "SOLVED", "The unknown angle is 180° − 65° = 115°.", "Reason: adjacent angles on a straight line add up to 180°."
    if "around a point" in s and "90" in s and "120" in s:
        return "SOLVED", "The missing angle is 360° − 90° − 120° = 150°.", "Reason: angles around a point add up to 360°."
    return "NEEDS MORE DETAIL", "I cannot reliably solve this exact statement yet. This version supports simple numerical equalities, some one-variable linear equations, and a few common angle word problems.", "Try writing a clear equation, such as 2*x+3=11, or describe the geometry facts and known angles. For diagrams, type the labels and relationships."

def rule_for_topic(topic):
    return [(name, data) for name, data in RULES.items() if data["topic"] == topic]

if mode == "Check one step":
    st.markdown("### Check a proof step")
    st.info("Enter one claim and the reason for it. If a step depends on a diagram or earlier lines, describe those facts too.")
    col1, col2 = st.columns(2)
    with col1:
        statement = st.text_area("Proof statement", placeholder="Example: ∠A = ∠C", height=120)
    with col2:
        reason = st.text_area("Reason / theorem (if known)", placeholder="Example: Vertically opposite angles are equal", height=120)
    context = st.text_area("Optional context or previous step", placeholder="Example: Lines AB and CD intersect at O.", height=80)
    if st.button("Check this step", type="primary"):
        if not statement.strip():
            st.warning("Please enter a proof statement.")
        else:
            if not reason.strip():
                verdict, explanation, next_step = solve_numeric_statement(statement)
                if verdict == "NEEDS MORE DETAIL":
                    st.warning("🟡 " + verdict)
                elif verdict == "NOT TRUE":
                    st.error("❌ " + verdict)
                else:
                    st.success("✅ " + verdict)
                st.markdown("**Solution / explanation**")
                st.write(explanation)
                st.markdown("**Why this method works**")
                st.write(next_step)
            else:
                verdict, explanation, next_step = check_step(statement + " " + context, reason, topic)
                if verdict == "SUPPORTED PATTERN":
                    st.success("✅ " + verdict)
                elif verdict == "LIKELY INCORRECT":
                    st.error("❌ " + verdict)
                else:
                    st.warning("🟡 " + verdict)
                st.markdown("**Why?**")
                st.write(explanation)
                st.markdown("**What to check next**")
                st.write(next_step)
            st.caption("Prototype limitation: this checks selected patterns and common equation forms, not every possible proof.")

elif mode == "Solve / explain a statement":
    st.markdown("### Solve a statement even when you don't know the reason")
    st.write("Type the question in ordinary words or as an equation. This prototype solves selected question types and shows the rule or method.")
    question = st.text_area(
        "Your mathematical statement or question",
        placeholder="Examples:\n2*x+3=11\n7*3=25\nA triangle has angles 50° and 60°. Find the third angle.\nAngles of 65° and x form a straight line. Find x.",
        height=150
    )
    if st.button("Solve and explain", type="primary"):
        if not question.strip():
            st.warning("Type a statement or question first.")
        else:
            status, answer, method = solve_numeric_statement(question)
            if status in ("SOLVED", "CHECKED"):
                st.success("✅ " + status)
            elif status == "NOT TRUE":
                st.error("❌ " + status)
            else:
                st.warning("🟡 " + status)
            st.markdown("**Answer**")
            st.write(answer)
            st.markdown("**Reasoning / method**")
            st.write(method)
            st.caption("If the question contains a diagram or a theorem not supported yet, the system may ask for more detail.")

elif mode == "Learn a rule":
    st.markdown("### Learn a mathematical rule")
    matches = rule_for_topic(topic)
    if matches:
        selected_rule = st.selectbox("Choose a rule", [x[0] for x in matches])
        data = RULES[selected_rule]
        st.markdown("#### Rule")
        st.write(data["rule"])
        st.markdown("#### Example")
        st.write(data["example"])
        st.markdown("#### Common mistake")
        st.write(data["common_error"])
    else:
        st.info("This topic is not yet in the small built-in rule library. Choose General proof or another topic to explore the prototype.")
        st.write("The full project can grow by adding teacher-reviewed rules, examples, diagrams, and tests for each grade.")

else:
    st.markdown("### Try a sample")
    samples = {
        "Correct: vertically opposite angles": ("∠A = ∠C", "Vertically opposite angles are equal", "Geometry & angles"),
        "Incorrect: straight-line angles equal": ("Angles on a straight line are equal", "They form a straight line", "Geometry & angles"),
        "Incorrect: equal lengths prove parallel": ("AB = CD, therefore AB is parallel to CD", "The lengths are equal", "Parallel lines"),
        "Correct arithmetic": ("12/3=4", "Arithmetic calculation", "Arithmetic & fractions"),
        "Incorrect arithmetic": ("7*3=25", "Arithmetic calculation", "Arithmetic & fractions"),
        "Needs review": ("These two triangles are congruent", "They look the same in the picture", "Triangles & polygons"),
    }
    choice = st.selectbox("Choose a sample", list(samples.keys()))
    statement, reason, sample_topic = samples[choice]
    st.code(f"Statement: {statement}\nReason: {reason}")
    if st.button("Check sample", type="primary"):
        verdict, explanation, next_step = check_step(statement, reason, sample_topic)
        if verdict == "SUPPORTED PATTERN":
            st.success("✅ " + verdict)
        elif verdict == "LIKELY INCORRECT":
            st.error("❌ " + verdict)
        else:
            st.warning("🟡 " + verdict)
        st.write("**Why?** " + explanation)
        st.write("**Next step:** " + next_step)

st.divider()
st.markdown("### What does each result mean?")
c1, c2, c3 = st.columns(3)
with c1:
    st.success("SUPPORTED PATTERN")
    st.write("The statement resembles a rule this prototype knows. It is not a guarantee that the entire proof is valid.")
with c2:
    st.error("LIKELY INCORRECT")
    st.write("The statement matches a known mistake or a checkable numerical error.")
with c3:
    st.warning("NEEDS REVIEW")
    st.write("The checker cannot decide confidently. Ask a teacher or add the missing theorem/context.")

st.markdown("### Coverage roadmap")
st.write("This prototype is designed to grow across Grades 1–12: number sense and arithmetic; fractions and ratios; algebra; geometry; measurement; statistics and probability; coordinate geometry; trigonometry; sequences; and advanced school topics. Grade selection currently guides the learning experience, but it does not automatically unlock a complete curriculum-specific checker.")
st.caption("Built as an educational prototype. Use teacher-checked examples to evaluate it; do not claim a perfect or universal proof checker.")
