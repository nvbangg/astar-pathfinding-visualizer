import json
import math
import os
from main import App

HEURISTICS = ['Euclidean', 'Manhattan', 'Octile', 'Chebyshev', 'Dijkstra (h=0)']

TEST_MODES = [
    ('T1_No_Diagonal',          {'allow_diag': False, 'dont_cross': False, 'diag_cost1': False}, 'no_diagonal'),
    ('T2_Diagonal_Normal',      {'allow_diag': True,  'dont_cross': False, 'diag_cost1': False}, 'diagonal_normal'),
    ('T3_Diagonal_Dont_Cross',  {'allow_diag': True,  'dont_cross': True,  'diag_cost1': False}, 'diagonal_dont_cross'),
    ('T4_Diagonal_Cost1',       {'allow_diag': True,  'dont_cross': False, 'diag_cost1': True }, 'diagonal_cost1'),
    ('T5_Diagonal_Cost1_Dont_Cross',{'allow_diag': True,  'dont_cross': True,  'diag_cost1': True }, 'diagonal_cost1_dont_cross'),
]

def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    test_file = os.path.join(base_dir, 'test_cases.json')

    if not os.path.exists(test_file):
        print(f"Error: {test_file} not found.")
        return

    with open(test_file, 'r', encoding='utf-8') as file:
        scenarios = json.load(file)

    total_passed = 0
    total_runs = 0

    for index, scenario in enumerate(scenarios, 1):
        print("-" * 10)
        print(f"SCENARIO {index}: {scenario['name']}\n")

        matrix = scenario['matrix']
        start_node = tuple(scenario['start'])
        end_node = tuple(scenario['end'])
        
        scenario_passed = 0
        scenario_runs = 0

        for mode_name, flags, key in TEST_MODES:
            expected = scenario['expected_costs'].get(key, None)
            if expected is None:
                continue

            print(f"[{mode_name}]")

            for heuristic in HEURISTICS:
                scenario_runs += 1
                total_runs += 1
                
                app = App()
                app.withdraw()
                app.grid_data = [row[:] for row in matrix]
                app.start_node = start_node
                app.end_node = end_node
                app.allow_diagonal.set(flags['allow_diag'])
                app.dont_cross_corners.set(flags['dont_cross'])
                app.diagonal_cost_one.set(flags['diag_cost1'])
                app.heuristic_combo.set(heuristic)
                
                result = app._run_astar_algorithm(heuristic_name=heuristic)
                app.destroy()

                actual = to_float(result.get('cost')) if result else None
                if actual is None:
                    actual = math.inf
                
                is_pass = abs(actual - expected) < 0.01
                heuristic_display = heuristic.replace(' (h=0)', '')
                
                if is_pass:
                    scenario_passed += 1
                    total_passed += 1
                    print(f"  - {heuristic_display:10}: PASS")
                else:
                    print(f"  - {heuristic_display:10}: FAIL (Expected: {expected:.2f}, Actual: {actual:.2f})")
            print()

        print(f"RESULT: {scenario_passed}/{scenario_runs} PASS.")
        print("-" * 10)

    print(f"FINAL RESULT: {total_passed}/{total_runs} PASS.")
    print("-" * 10)

if __name__ == '__main__':
    main()