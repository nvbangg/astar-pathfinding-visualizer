import json
import math
import os
from main import App

HEURISTICS = ['Euclidean', 'Manhattan', 'Octile', 'Chebyshev', 'Dijkstra (h=0)']
TEST_MODES = [
    ('T1_No_Diagonal',           False, False, False, 'no_diagonal'),
    ('T2_Diagonal_Normal',       True,  False, False, 'diagonal_normal'),
    ('T3_Diagonal_Dont_Cross',   True,  True,  False, 'diagonal_dont_cross'),
    ('T4_Diagonal_Cost1',        True,  False, True,  'diagonal_cost1'),
    ('T5_Diagonal_Cost1_Dont_Cross', True, True, True,  'diagonal_cost1_dont_cross'),
]

def main():
    file_path = os.path.join(os.path.dirname(__file__), 'test_cases.json')
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as file:
        scenarios = json.load(file)

    app_instance = App()
    app_instance.withdraw() # Ẩn cửa sổ giao diện

    total_passed = 0
    total_runs = 0

    for index, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*15} SCENARIO {index}: {scenario['name']} {'='*15}")
        
        matrix = scenario['matrix']
        start_node = tuple(scenario['start'])
        end_node = tuple(scenario['end'])
        
        for mode_name, allow_diag, dont_cross, cost_one, json_key in TEST_MODES:
            expected_data = scenario['expected_costs'].get(json_key)
            if expected_data is None:
                continue

            print(f"\n[{mode_name}]")
            for heuristic in HEURISTICS:
                # Lấy giá trị expected cụ thể cho heuristic nếu có, ngược lại dùng default
                if isinstance(expected_data, dict):
                    h_name_key = heuristic.split(' (')[0]
                    expected_cost = expected_data.get(h_name_key, expected_data.get('default'))
                else:
                    expected_cost = expected_data

                if expected_cost is None:
                    continue

                # Cấu hình App cho test case hiện tại
                app_instance.grid_data = [row[:] for row in matrix]
                app_instance.start_node = start_node
                app_instance.end_node = end_node
                app_instance.allow_diagonal.set(allow_diag)
                app_instance.dont_cross_corners.set(dont_cross)
                app_instance.diagonal_cost_one.set(cost_one)
                app_instance.combobox_heuristic.set(heuristic)

                # Chạy thuật toán và lấy kết quả
                result, _ = app_instance._run_astar_algorithm(heuristic_name=heuristic)
                
                try:
                    actual_cost = float(result.get('path_cost', 'inf'))
                except (ValueError, TypeError):
                    actual_cost = math.inf

                # So sánh kết quả với sai số cho phép 0.01
                is_passed = math.isclose(actual_cost, expected_cost, abs_tol=0.01)
                
                status = "PASS" if is_passed else f"FAIL (Expected: {expected_cost:.2f}, Actual: {actual_cost:.2f})"
                heuristic_name = heuristic.replace(' (h=0)', '')
                print(f"  - {heuristic_name:10}: {status}")

                total_runs += 1
                if is_passed:
                    total_passed += 1

    app_instance.destroy()
    print(f"\n{'='*40}\nFINAL RESULT: {total_passed}/{total_runs} PASSED.\n{'='*40}")

if __name__ == '__main__':
    main()