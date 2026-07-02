# FinFlutter

**Constrained fin-design optimizer for high-power rockets — maximizes apogee while meeting minimum flutter-margin and static-stability requirements, using OpenRocket for flight simulation.**

> ⚠️ **Status: early development.** See the [Roadmap](#roadmap) for what works today versus what''s planned.

---

## What it does

FinFlutter is a constrained optimization tool for high-power rocket fins. You give it a set of conditions — motor, airframe, flight envelope, and the minimum margins you''re willing to accept — and it searches fin geometries to find the design that reaches the **highest apogee** while still satisfying:

- a **minimum flutter margin** (the fin must not flutter below a safety-factored max velocity), and
- a **minimum static-stability caliber** (the rocket must stay controllably stable).

Apogee and stability come from [OpenRocket](https://openrocket.info/) via automated simulation; flutter speed is computed from an aeroelastic model built into the tool.

## Why this is an optimization problem, not a calculation

The interesting part is that the constraints fight the objective:

- **Bigger fins** buy stability margin but add drag and *lower* apogee.
- **Smaller or thinner fins** cut drag and *raise* apogee — but push the design toward the flutter boundary.

If there were no tension, the "best" fin would just be the smallest one. Because stability pulls one way, drag pulls another, and flutter sets a hard floor on how thin you can go, the optimal fin lives at the intersection of competing constraints. FinFlutter searches that trade space instead of guessing at it.

## How it works
The optimizer proposes a fin geometry, evaluates it through both the OpenRocket simulation and the flutter model, rejects any design that violates the stability or flutter constraints, and searches for the feasible design with maximum apogee.

## The flutter model

Flutter speed is computed using the NACA TN 4197 method.

> **Note:** the TN 4197 implementation uses a corrected form of the published formula. The original denominator constant is only valid for symmetric fin sections; the code accounts for this.

## Installation

**Requirements**

- Python 3.9+
- A Java runtime (JDK 17) — required by JPype to run OpenRocket headlessly
- `OpenRocket-23.09.jar` — provided separately (not committed to this repo)

**Setup**

```bash
git clone https://github.com/emiliasanchezdecotto2029-rgb/fin-flutter-optimizer.git
cd fin-flutter-optimizer
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

**OpenRocket / JPype notes**

- Download `OpenRocket-23.09.jar` and place it in the project folder. It is **not** included in this repo.
- If JPype can''t find your JDK, set a `JAVA_HOME` environment variable pointing to your JDK install.
- Verify the bridge works before running anything else: load a `.ork` file and run one simulation. If that succeeds, the setup is good.

## Usage

> _To be documented as the CLI/interface is built._

## Validation

A tool that predicts flutter is only trustworthy if it''s validated. Planned validation:

- **Flutter model** — reproduce published flutter speeds from standard references to confirm the TN 4197 implementation is correct.
- **OpenRocket coupling** — confirm apogee and stability outputs match manual OpenRocket runs for known designs.

## Roadmap

- [x] OpenRocket <-> Python bridge working end-to-end (orlab + JPype)
- [ ] NACA TN 4197 flutter calculation
- [ ] Optimizer loop: maximize apogee subject to flutter + stability constraints
- [ ] Validation against published flutter cases

## License

MIT — see [LICENSE](LICENSE).
