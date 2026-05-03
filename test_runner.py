import json
import math
import os
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

def format_result(ok, expected, actual):
    if ok:
        return "PASS"
    return f"FAIL (Expected: {expected:.2f}, Actual: {actual:.2f})"

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(base_dir, 'test_cases.json')

    with open(test_file, 'r', encoding='utf-8') as f:
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
                # --- Run Bi:OFF ---
                total += 1
                app = App()
                app.withdraw()
                app.ROWS = rows
                app.COLS = cols
                app.grid_data = [row[:] for row in matrix]
                app.start = start
                app.end = end
                app.allow_diag.set(flags['allow_diag'])
                app.cross_corner.set(flags['dont_cross'])
                app.diag_cost1.set(flags['diag_cost1'])
                app.heuristic.set(heur)
                app.bidir.set(False)
                app.running = True
                result_off = run_one(app, heur, False)
                app.destroy()

                actual_off = to_float(result_off.get('cost')) if result_off else None
                if actual_off is None:
                    actual_off = math.inf
                ok_off = abs(actual_off - expected) < 0.01
                if ok_off:
                    passed += 1

                # --- Run Bi:ON ---
                total += 1
                app = App()
                app.withdraw()
                app.ROWS = rows
                app.COLS = cols
                app.grid_data = [row[:] for row in matrix]
                app.start = start
                app.end = end
                app.allow_diag.set(flags['allow_diag'])
                app.cross_corner.set(flags['dont_cross'])
                app.diag_cost1.set(flags['diag_cost1'])
                app.heuristic.set(heur)
                app.bidir.set(True)
                app.running = True
                result_on = run_one(app, heur, True)
                app.destroy()

                actual_on = to_float(result_on.get('cost')) if result_on else None
                if actual_on is None:
                    actual_on = math.inf
                ok_on = abs(actual_on - expected) < 0.01
                if ok_on:
                    passed += 1

                heur_name = heur.replace(' (h=0)', '')
                left = format_result(ok_off, expected, actual_off)
                right = format_result(ok_on, expected, actual_on)

                print(f"  - {heur_name:<10} (Bi:OFF): {left}  | (Bi:ON): {right}")
            print()

    print(f"RESULT: {passed}/{total} PASS.")
    print("-" * 10)

if __name__ == '__main__':
    main()