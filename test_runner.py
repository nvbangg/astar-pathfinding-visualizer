import json
import math
from main import App

HEURISTICS = ['Euclidean', 'Manhattan', 'Octile', 'Chebyshev', 'Dijkstra (h=0)']

TEST_MODES = [
    ('T1_No_Diag',              {'allow_diag': False, 'dont_cross': False, 'diag_cost1': False}, 'no_diagonal'),
    ('T2_Diag_Normal',          {'allow_diag': True,  'dont_cross': False, 'diag_cost1': False}, 'diagonal_normal'),
    ('T3_Diag_Dont_Cross',      {'allow_diag': True,  'dont_cross': True,  'diag_cost1': False}, 'diagonal_dont_cross'),
    ('T4_Diag_Cost1_Normal',    {'allow_diag': True,  'dont_cross': False, 'diag_cost1': True }, 'diagonal_cost1'),
    ('T5_Diag_Cost1_Dont_Cross',{'allow_diag': True,  'dont_cross': True,  'diag_cost1': True }, 'diagonal_cost1_dont_cross'),
]

def to_float(val):
    try:
        return float(val)
    except:
        return None

def run_one(app, heuristic, bidir):
    if bidir:
        return app._run_bidir(hname=heuristic, instant=True)
    return app._run_astar(hname=heuristic, instant=True)

def print_line(heur, bi, passed, expected, actual):
    if passed:
        print(f"  - {heur:<10} (Bi:{bi}): PASS")
    else:
        print(f"  - {heur:<10} (Bi:{bi}): FAIL (Expected: {expected:.2f}, Actual: {actual:.2f})")

def main():
    with open(r'd:\AI\test_cases.json', 'r', encoding='utf-8') as f:
        scenarios = json.load(f)

    total = 0
    passed = 0

    for idx, sc in enumerate(scenarios, 1):
        print("-" * 10)
        print(f"SCENARIO {idx}: {sc['name']}\n")

        matrix = sc['matrix']
        rows = len(matrix)
        cols = len(matrix[0]) if rows else 0
        start = tuple(sc['start'])
        end = tuple(sc['end'])

        for mode_name, flags, key in TEST_MODES:
            expected = sc['expected_costs'].get(key, None)
            if expected is None:
                continue

            print(f"[{mode_name}]")
            for heur in HEURISTICS:
                for bi in ('OFF', 'ON'):
                    total += 1
                    app = App()
                    app.withdraw()

                    # Setup grid
                    app.ROWS = rows
                    app.COLS = cols
                    app.grid_data = [row[:] for row in matrix]
                    app.start = start
                    app.end = end

                    # Flags
                    app.allow_diag.set(flags['allow_diag'])
                    app.cross_corner.set(flags['dont_cross'])
                    app.diag_cost1.set(flags['diag_cost1'])
                    app.heuristic.set(heur)
                    app.bidir.set(bi == 'ON')
                    app.running = True

                    result = run_one(app, heur, bi == 'ON')
                    app.destroy()

                    actual = to_float(result.get('cost')) if result else None
                    if actual is None:
                        actual = math.inf

                    ok = abs(actual - expected) < 0.01
                    if ok:
                        passed += 1

                    print_line(heur.replace(' (h=0)',''), bi, ok, expected, actual)
            print()

    print(f"RESULT: {passed}/{total} PASS.")
    print("-" * 10)

if __name__ == '__main__':
    main()