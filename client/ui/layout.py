import gradio as gr
from gradio_modal import Modal

from ui.actions import (
    add_constraint,
    add_objective_coefficient,
    add_variable,
    arm_delete,
    cancel_delete,
    handle_overwrite,
    handle_rename,
    hide_panel,
    load_selected_solution,
    show_panel,
    solve_from_ui,
    solve_only,
    toggle_preview,
    update_history_summary,
    initialize_saved_data,
)

from ui.topsis_actions import (
    initialize_topsis_saved_data,
    update_topsis_history_summary,
    add_criteria,
    sync_alternatives_columns,
    solve_topsis_from_ui,
    handle_topsis_overwrite,
    handle_topsis_rename,
    solve_topsis_only,
    load_selected_topsis_solution,
    topsis_arm_delete,
    topsis_cancel_delete,
)

from ui.electre_actions import (
    initialize_electre_saved_data,
    update_electre_history_summary,
    add_electre_criteria,
    sync_electre_alternatives_columns,
    solve_electre_from_ui,
    handle_electre_overwrite,
    handle_electre_rename,
    solve_electre_only,
    load_selected_electre_solution,
    electre_arm_delete,
    electre_cancel_delete,
)

def create_app():
    with gr.Blocks(theme=gr.Theme.from_hub("hmb/spark"), title="Оптимизация") as app:
        gr.Markdown("# Minimaxer")

        with gr.Tabs():
            
            with gr.Tab("Еднокритериална Оптимизация"):
                saved_solutions = gr.BrowserState(
                    storage_key="minimaxer_history",
                    secret="minimaxer-history-secret-v1",
                    default_value={},
                )
                pending_request = gr.State({})
                delete_armed = gr.State(False)

                with gr.Row():
                    
                    with gr.Column(scale=1, min_width=300):
                        gr.Markdown("## Управление на задачи")

                        with gr.Group(visible=False) as conflict_ui:
                            gr.Markdown("### ⚠️ Име вече съществува")
                            gr.Markdown("Задача с това име вече е запазена. Изберете действие:")
                            with gr.Row():
                                overwrite_btn = gr.Button("Презапиши", variant="primary")
                            gr.Markdown("--- или запишете с ново име ---")
                            new_name_input = gr.Textbox(label="Ново име", placeholder="Въведете ново име...")
                            rename_save_btn = gr.Button("Запази с ново име", variant="secondary")

                        gr.Markdown("### Запазени решения")
                        saved_list = gr.Radio(
                            label="Изберете задача",
                            choices=[],
                            interactive=True,
                            container=True,
                        )

                        with gr.Row():
                            delete_btn = gr.Button("Изтрий избраната", variant="stop", scale=2)
                            delete_cancel_btn = gr.Button("Отказ", variant="secondary", scale=1, visible=False)

                        delete_hint = gr.Markdown("", visible=False)

                        gr.Markdown("### Обобщение на историята")
                        history_summary = gr.Markdown("Няма запазени решения.")

                    
                    with gr.Column(scale=3):
                        with gr.Tabs():
                            with gr.Tab("1. Модел и Променливи"):
                                with gr.Row():
                                    problem_name = gr.Textbox(
                                        label="Име на задача",
                                        value="Примерна задача",
                                        scale=2,
                                    )
                                    direction = gr.Radio(
                                        label="Посока на оптимизация",
                                        choices=[("Максимизиране", "maximize"), ("Минимизиране", "minimize")],
                                        value="maximize",
                                        scale=1,
                                    )

                                gr.Markdown("### Дефиниране на променливи")
                                open_variable_panel_btn = gr.Button("Добави променлива", variant="secondary")

                                with Modal(visible=False) as variable_panel:
                                    gr.Markdown("### Нова променлива")
                                    with gr.Row():
                                        variable_name_input = gr.Textbox(label="Име", placeholder="x1")
                                        variable_low_input = gr.Textbox(label="Долна граница", placeholder="напр. 0 (или оставете празно)")
                                        variable_up_input = gr.Textbox(label="Горна граница", placeholder="напр. 100 (или оставете празно)")

                                    variable_category_input = gr.Dropdown(
                                        label="Категория",
                                        choices=[("Непрекъсната", "Continuous"),
                                                 ("Целочислена", "Integer"),
                                                 ("Булева", "Binary")],
                                        value="Continuous",
                                    )
                                    with gr.Row():
                                        add_variable_btn = gr.Button("Добави", variant="primary")
                                        cancel_variable_btn = gr.Button("Отказ")

                                variables_table = gr.Dataframe(
                                    label="Списък с променливи",
                                    headers=["име", "долна граница", "горна граница", "категория"],
                                    datatype=["str", "str", "str", "str"],
                                    value=[
                                        ["x", "", "", "Continuous"],
                                        ["y", "", "", "Continuous"],
                                    ],
                                    row_count=(2, "dynamic"),
                                    col_count=(4, "fixed"),
                                    interactive=True,
                                )

                            with gr.Tab("2. Целева функция и Ограничения"):
                                with gr.Row():
                                    with gr.Column():
                                        gr.Markdown("### Целева функция")
                                        open_objective_panel_btn = gr.Button("Добави коефициент", variant="secondary")

                                        with Modal(visible=False) as objective_panel:
                                            gr.Markdown("### Добавяне към целевата функция")
                                            gr.Markdown("Пример: За 5x изберете променлива x и въведете коефициент 5.")
                                            with gr.Row():
                                                objective_variable_input = gr.Dropdown(label="Променлива", choices=["x", "y"])
                                                objective_coefficient_input = gr.Textbox(label="Коефициент", placeholder="Напр. 5")
                                            with gr.Row():
                                                add_objective_btn = gr.Button("Добави", variant="primary")
                                                cancel_objective_btn = gr.Button("Отказ")

                                        objective_table = gr.Dataframe(
                                            label="Коефициенти",
                                            headers=["променлива", "коефициент"],
                                            datatype=["str", "str"],
                                            value=[["x", 0], ["y", 0]],
                                            row_count=(2, "dynamic"),
                                            col_count=(2, "fixed"),
                                            interactive=True,
                                        )

                                    with gr.Column():
                                        gr.Markdown("### Ограничения")
                                        open_constraint_panel_btn = gr.Button("Добави ограничение", variant="secondary")

                                        with Modal(visible=False) as constraint_panel:
                                            gr.Markdown("### Ново ограничение")
                                            gr.Markdown("Пример: За 2x + y <= 10 въведете коефициенти x:2,y:1")

                                            constraint_name_input = gr.Textbox(label="Име", placeholder="c1")
                                            constraint_coefficients_input = gr.Textbox(label="Коефициенти", placeholder="x:2,y:1")

                                            with gr.Row():
                                                constraint_operator_input = gr.Radio(
                                                    label="Оператор",
                                                    choices=["<=", ">=", "=="],
                                                    value="<=",
                                                )
                                                constraint_rhs_input = gr.Textbox(label="Дясна страна", placeholder="Напр. 10")

                                            with gr.Row():
                                                add_constraint_btn = gr.Button("Добави", variant="primary")
                                                cancel_constraint_btn = gr.Button("Отказ")

                                        constraints_table = gr.Dataframe(
                                            label="Списък с ограничения",
                                            headers=["име", "коефициенти", "оператор", "дясна страна"],
                                            datatype=["str", "str", "str", "str"],
                                            value=[
                                                ["c1", "x:2,y:1", "<=", 10],
                                                ["c2", "x:1,y:1", "<=", 7],
                                            ],
                                            row_count=(2, "dynamic"),
                                            col_count=(4, "fixed"),
                                            interactive=True,
                                        )

                            with gr.Tab("3. Преглед и Решаване"):
                                with gr.Row():
                                    preview_btn = gr.Button("Преглед на модела")
                                    solve_btn = gr.Button("Реши и Запази", variant="primary")
                                    solve_only_btn = gr.Button("Реши", variant="primary")

                                preview_output = gr.Markdown(label="Математически преглед", visible=False)
                                status_message = gr.Textbox(label="Статус", interactive=False)

                                gr.Markdown("### Резултати")
                                objective_value_output = gr.Textbox(label="Оптимална стойност на целевата функция", interactive=False)
                                result_table = gr.Dataframe(
                                    label="Стойности на променливите",
                                    headers=["име", "стойност"],
                                    interactive=False,
                                )

                                with gr.Accordion("Детайли от заявката (JSON)", open=False):
                                    with gr.Row():
                                        request_output = gr.JSON(label="Изпратена заявка")
                                        response_output = gr.JSON(label="Отговор от решаващия модул")

                            with gr.Tab("4. Запазени решения (Детайли)"):
                                gr.Markdown("### Преглед на запазени данни")
                                with gr.Row():
                                    saved_request_output = gr.JSON(label="Запазена заявка")
                                    saved_response_output = gr.JSON(label="Запазен отговор")

            
            with gr.Tab("TOPSIS"):
                t_saved_solutions = gr.BrowserState(
                    storage_key="minimaxer_topsis_history",
                    secret="minimaxer-topsis-history-secret-v1",
                    default_value={},
                )
                t_pending_request = gr.State({})
                t_delete_armed = gr.State(False)

                with gr.Row():
                    
                    with gr.Column(scale=1, min_width=300):
                        gr.Markdown("## Управление на TOPSIS задачи")

                        with gr.Group(visible=False) as t_conflict_ui:
                            gr.Markdown("### ⚠️ Името вече съществува")
                            gr.Markdown("Задача с това име вече е запазена. Изберете действие:")
                            with gr.Row():
                                t_overwrite_btn = gr.Button("Презапиши", variant="primary")
                            gr.Markdown("--- или запишете с ново име ---")
                            t_new_name_input = gr.Textbox(label="Ново име", placeholder="Въведете ново име...")
                            t_rename_save_btn = gr.Button("Запази с ново име", variant="secondary")

                        gr.Markdown("### Запазени решения")
                        t_saved_list = gr.Radio(
                            label="Изберете задача",
                            choices=[],
                            interactive=True,
                            container=True,
                        )

                        with gr.Row():
                            t_delete_btn = gr.Button("Изтрий избраната", variant="stop", scale=2)
                            t_delete_cancel_btn = gr.Button("Отказ", variant="secondary", scale=1, visible=False)

                        t_delete_hint = gr.Markdown("", visible=False)

                        gr.Markdown("### Обобщение на историята")
                        t_history_summary = gr.Markdown("Няма запазени TOPSIS решения.")

                    
                    with gr.Column(scale=3):
                        with gr.Tabs():
                            with gr.Tab("1. Критерии"):
                                t_problem_name = gr.Textbox(
                                    label="Име на задача",
                                    value="Примерна TOPSIS задача",
                                    scale=2,
                                )

                                gr.Markdown("### Дефиниране на критерии")
                                t_open_crit_panel_btn = gr.Button("Добави критерий", variant="secondary")

                                with Modal(visible=False) as t_crit_panel:
                                    gr.Markdown("### Нов критерий")
                                    with gr.Row():
                                        t_crit_name_input = gr.Textbox(label="Име", placeholder="цена")
                                        t_crit_weight_input = gr.Textbox(label="Тежест", placeholder="напр. 0.4")
                                    t_crit_direction_input = gr.Dropdown(
                                        label="Посока",
                                        choices=[("Максимизиране (maximize)", "maximize"),
                                                 ("Минимизиране (minimize)", "minimize")],
                                        value="maximize",
                                    )
                                    with gr.Row():
                                        t_add_crit_btn = gr.Button("Добави", variant="primary")
                                        t_cancel_crit_btn = gr.Button("Отказ")

                                t_criteria_table = gr.Dataframe(
                                    label="Списък с критерии",
                                    headers=["име", "посока", "тежест"],
                                    datatype=["str", "str", "number"],
                                    value=[
                                        ["цена", "minimize", 0.4],
                                        ["качество", "maximize", 0.6],
                                    ],
                                    row_count=(2, "dynamic"),
                                    col_count=(3, "fixed"),
                                    interactive=True,
                                )

                            with gr.Tab("2. Алтернативи"):
                                gr.Markdown("### Дефиниране на алтернативи")
                                gr.Markdown("Попълнете стойностите за всяка алтернатива по съответните критерии.")
                                
                                t_sync_btn = gr.Button("Синхронизирай колони (Ако сте променили критериите ръчно)", variant="secondary")
                                
                                t_alternatives_table = gr.Dataframe(
                                    label="Алтернативи",
                                    headers=["Име на алтернатива", "цена", "качество"],
                                    datatype="str", 
                                    value=[
                                        ["Алт 1", "200", "8"],
                                        ["Алт 2", "150", "6"],
                                    ],
                                    interactive=True,
                                )

                            with gr.Tab("3. Решаване и Резултати"):
                                with gr.Row():
                                    t_solve_btn = gr.Button("Реши и Запази", variant="primary")
                                    t_solve_only_btn = gr.Button("Реши", variant="primary")

                                t_status_message = gr.Textbox(label="Статус", interactive=False)

                                gr.Markdown("### Класиране (Rankings)")
                                t_result_table = gr.Dataframe(
                                    label="Резултати",
                                    headers=["Ранг", "Име на алтернатива", "Относителна близост"],
                                    interactive=False,
                                )

                                with gr.Accordion("Детайли от заявката (JSON)", open=False):
                                    with gr.Row():
                                        t_request_output = gr.JSON(label="Изпратена заявка")
                                        t_response_output = gr.JSON(label="Отговор от решаващия модул")

                            with gr.Tab("4. Запазени решения (Детайли)"):
                                gr.Markdown("### Преглед на запазени данни")
                                with gr.Row():
                                    t_saved_request_output = gr.JSON(label="Запазена заявка")
                                    t_saved_response_output = gr.JSON(label="Запазен отговор")

            with gr.Tab("ELECTRE I"):
                e_saved_solutions = gr.BrowserState(
                    storage_key="minimaxer_electre_history",
                    secret="minimaxer-electre-history-secret-v1",
                    default_value={},
                )
                e_pending_request = gr.State({})
                e_delete_armed = gr.State(False)

                with gr.Row():

                    with gr.Column(scale=1, min_width=300):
                        gr.Markdown("## Управление на ELECTRE задачи")

                        with gr.Group(visible=False) as e_conflict_ui:
                            gr.Markdown("### ⚠️ Името вече съществува")
                            gr.Markdown("Задача с това име вече е запазена. Изберете действие:")
                            with gr.Row():
                                e_overwrite_btn = gr.Button("Презапиши", variant="primary")
                            gr.Markdown("--- или запишете с ново име ---")
                            e_new_name_input = gr.Textbox(label="Ново име", placeholder="Въведете ново име...")
                            e_rename_save_btn = gr.Button("Запази с ново име", variant="secondary")

                        gr.Markdown("### Запазени решения")
                        e_saved_list = gr.Radio(
                            label="Изберете задача",
                            choices=[],
                            interactive=True,
                            container=True,
                        )

                        with gr.Row():
                            e_delete_btn = gr.Button("Изтрий избраната", variant="stop", scale=2)
                            e_delete_cancel_btn = gr.Button("Отказ", variant="secondary", scale=1, visible=False)

                        e_delete_hint = gr.Markdown("", visible=False)

                        gr.Markdown("### Обобщение на историята")
                        e_history_summary = gr.Markdown("Няма запазени ELECTRE решения.")

                    with gr.Column(scale=3):
                        with gr.Tabs():
                            with gr.Tab("1. Критерии"):
                                e_problem_name = gr.Textbox(
                                    label="Име на задача",
                                    value="Примерна ELECTRE задача",
                                    scale=2,
                                )

                                gr.Markdown("### Дефиниране на критерии")
                                e_open_crit_panel_btn = gr.Button("Добави критерий", variant="secondary")

                                with Modal(visible=False) as e_crit_panel:
                                    gr.Markdown("### Нов критерий")
                                    with gr.Row():
                                        e_crit_name_input = gr.Textbox(label="Име", placeholder="цена")
                                        e_crit_weight_input = gr.Textbox(label="Тежест", placeholder="напр. 0.4")
                                    with gr.Row():
                                        e_crit_direction_input = gr.Dropdown(
                                            label="Посока",
                                            choices=[("Максимизиране (maximize)", "maximize"),
                                                     ("Минимизиране (minimize)", "minimize")],
                                            value="maximize",
                                        )
                                        e_crit_type_input = gr.Dropdown(
                                            label="Тип",
                                            choices=[("Количествен (quantitative)", "quantitative"),
                                                     ("Качествен (qualitative)", "qualitative")],
                                            value="quantitative",
                                        )
                                    with gr.Row():
                                        e_add_crit_btn = gr.Button("Добави", variant="primary")
                                        e_cancel_crit_btn = gr.Button("Отказ")

                                e_criteria_table = gr.Dataframe(
                                    label="Списък с критерии",
                                    headers=["име", "посока", "тежест", "тип"],
                                    datatype=["str", "str", "number", "str"],
                                    value=[
                                        ["цена", "minimize", 0.4, "quantitative"],
                                        ["качество", "maximize", 0.6, "qualitative"],
                                    ],
                                    row_count=(2, "dynamic"),
                                    col_count=(4, "fixed"),
                                    interactive=True,
                                )

                            with gr.Tab("2. Алтернативи"):
                                gr.Markdown("### Дефиниране на алтернативи")
                                gr.Markdown("Попълнете стойностите за всяка алтернатива по съответните критерии. За качествени критерии използвайте числова скала (напр. 1–5).")

                                e_sync_btn = gr.Button("Синхронизирай колони (Ако сте променили критериите ръчно)", variant="secondary")

                                e_alternatives_table = gr.Dataframe(
                                    label="Алтернативи",
                                    headers=["Име на алтернатива", "цена", "качество"],
                                    datatype="str",
                                    value=[
                                        ["Алт 1", "200", "5"],
                                        ["Алт 2", "150", "3"],
                                    ],
                                    interactive=True,
                                )

                            with gr.Tab("3. Решаване и Резултати"):
                                gr.Markdown("### Прагове на ELECTRE I")
                                with gr.Row():
                                    e_concordance_threshold = gr.Number(
                                        label="Праг на съгласие (c*)",
                                        value=0.7,
                                        minimum=0.0,
                                        maximum=1.0,
                                        step=0.05,
                                    )
                                    e_discordance_threshold = gr.Number(
                                        label="Праг на несъгласие (d*)",
                                        value=0.3,
                                        minimum=0.0,
                                        maximum=1.0,
                                        step=0.05,
                                    )

                                with gr.Row():
                                    e_solve_btn = gr.Button("Реши и Запази", variant="primary")
                                    e_solve_only_btn = gr.Button("Реши", variant="primary")

                                e_status_message = gr.Textbox(label="Статус", interactive=False)

                                gr.Markdown("### Резултати")
                                e_kernel_output = gr.Markdown("Ядрото ще се покаже тук след решаване.")
                                e_result_table = gr.Dataframe(
                                    label="Отношения на превъзходство",
                                    headers=["Превъзхожда", "Превъзхождан", "Съгласие (C)", "Несъгласие (D)"],
                                    interactive=False,
                                )

                                with gr.Accordion("Детайли от заявката (JSON)", open=False):
                                    with gr.Row():
                                        e_request_output = gr.JSON(label="Изпратена заявка")
                                        e_response_output = gr.JSON(label="Отговор от решаващия модул")

                            with gr.Tab("4. Запазени решения (Детайли)"):
                                gr.Markdown("### Преглед на запазени данни")
                                with gr.Row():
                                    e_saved_request_output = gr.JSON(label="Запазена заявка")
                                    e_saved_response_output = gr.JSON(label="Запазен отговор")

        
        solve_outputs = [
            conflict_ui, pending_request, response_output,
            objective_value_output, result_table,
            request_output, saved_solutions, saved_list, history_summary, status_message,
        ]

        saved_solutions.change(
            fn=update_history_summary,
            inputs=saved_solutions,
            outputs=history_summary,
        )
        saved_solutions.change(
            fn=lambda s: gr.update(choices=list(s.keys()) if s else []),
            inputs=saved_solutions,
            outputs=saved_list,
        )

        app.load(
            fn=initialize_saved_data,
            inputs=[saved_solutions],
            outputs=[history_summary, saved_list],
        )

        open_variable_panel_btn.click(fn=show_panel, outputs=variable_panel)
        cancel_variable_btn.click(fn=hide_panel, outputs=variable_panel)
        add_variable_btn.click(
            fn=add_variable,
            inputs=[variable_name_input, variable_low_input, variable_up_input, variable_category_input, variables_table, objective_table],
            outputs=[variables_table, objective_table, objective_variable_input, variable_name_input, variable_low_input, variable_up_input, variable_category_input, variable_panel],
        )

        open_objective_panel_btn.click(fn=show_panel, outputs=objective_panel)
        cancel_objective_btn.click(fn=hide_panel, outputs=objective_panel)
        add_objective_btn.click(
            fn=add_objective_coefficient,
            inputs=[objective_variable_input, objective_coefficient_input, objective_table],
            outputs=[objective_table, objective_variable_input, objective_coefficient_input, objective_panel],
        )

        open_constraint_panel_btn.click(fn=show_panel, outputs=constraint_panel)
        cancel_constraint_btn.click(fn=hide_panel, outputs=constraint_panel)
        add_constraint_btn.click(
            fn=add_constraint,
            inputs=[constraint_name_input, constraint_coefficients_input, constraint_operator_input, constraint_rhs_input, constraints_table],
            outputs=[constraints_table, constraint_name_input, constraint_coefficients_input, constraint_operator_input, constraint_rhs_input, constraint_panel],
        )

        preview_btn.click(
            fn=toggle_preview,
            inputs=[preview_btn, problem_name, direction, variables_table, objective_table, constraints_table],
            outputs=[preview_output, preview_btn],
        )

        solve_btn.click(
            fn=solve_from_ui,
            inputs=[problem_name, direction, variables_table, objective_table, constraints_table, saved_solutions],
            outputs=solve_outputs,
        )

        solve_only_btn.click(
            fn=solve_only,
            inputs=[problem_name, direction, variables_table, objective_table, constraints_table],
            outputs=solve_outputs,
        )

        overwrite_btn.click(
            fn=handle_overwrite,
            inputs=[pending_request, saved_solutions],
            outputs=solve_outputs,
        )

        rename_save_btn.click(
            fn=handle_rename,
            inputs=[new_name_input, pending_request, saved_solutions],
            outputs=solve_outputs,
        )

        saved_list.change(
            fn=load_selected_solution,
            inputs=[saved_list, saved_solutions],
            outputs=[problem_name, direction, variables_table, objective_table, constraints_table, response_output, saved_request_output, saved_response_output, objective_value_output, result_table, request_output, status_message],
        ).then(
            fn=cancel_delete,
            outputs=[delete_armed, delete_btn, delete_cancel_btn, delete_hint],
        )

        delete_btn.click(
            fn=arm_delete,
            inputs=[saved_list, delete_armed, saved_solutions],
            outputs=[delete_armed, delete_btn, delete_cancel_btn, delete_hint, saved_solutions, saved_list, history_summary, status_message],
        )

        delete_cancel_btn.click(
            fn=cancel_delete,
            outputs=[delete_armed, delete_btn, delete_cancel_btn, delete_hint],
        )

        
        t_solve_outputs = [
            t_conflict_ui, t_pending_request, t_response_output,
            t_result_table, t_request_output, t_saved_solutions,
            t_saved_list, t_history_summary, t_status_message,
        ]

        t_saved_solutions.change(
            fn=update_topsis_history_summary,
            inputs=t_saved_solutions,
            outputs=t_history_summary,
        )
        t_saved_solutions.change(
            fn=lambda s: gr.update(choices=list(s.keys()) if s else []),
            inputs=t_saved_solutions,
            outputs=t_saved_list,
        )

        app.load(
            fn=initialize_topsis_saved_data,
            inputs=[t_saved_solutions],
            outputs=[t_history_summary, t_saved_list],
        )

        t_open_crit_panel_btn.click(fn=show_panel, outputs=t_crit_panel)
        t_cancel_crit_btn.click(fn=hide_panel, outputs=t_crit_panel)
        t_add_crit_btn.click(
            fn=add_criteria,
            inputs=[t_crit_name_input, t_crit_direction_input, t_crit_weight_input, t_criteria_table, t_alternatives_table],
            outputs=[t_criteria_table, t_alternatives_table, t_crit_name_input, t_crit_direction_input, t_crit_weight_input, t_crit_panel],
        )
        
        t_sync_btn.click(
            fn=sync_alternatives_columns,
            inputs=[t_criteria_table, t_alternatives_table],
            outputs=[t_alternatives_table],
        )

        t_solve_btn.click(
            fn=solve_topsis_from_ui,
            inputs=[t_problem_name, t_criteria_table, t_alternatives_table, t_saved_solutions],
            outputs=t_solve_outputs,
        )

        t_solve_only_btn.click(
            fn=solve_topsis_only,
            inputs=[t_problem_name, t_criteria_table, t_alternatives_table],
            outputs=t_solve_outputs,
        )

        t_overwrite_btn.click(
            fn=handle_topsis_overwrite,
            inputs=[t_pending_request, t_saved_solutions],
            outputs=t_solve_outputs,
        )

        t_rename_save_btn.click(
            fn=handle_topsis_rename,
            inputs=[t_new_name_input, t_pending_request, t_saved_solutions],
            outputs=t_solve_outputs,
        )

        t_saved_list.change(
            fn=load_selected_topsis_solution,
            inputs=[t_saved_list, t_saved_solutions],
            outputs=[t_problem_name, t_criteria_table, t_alternatives_table, t_response_output, t_saved_request_output, t_saved_response_output, t_result_table, t_request_output, t_status_message],
        ).then(
            fn=topsis_cancel_delete,
            outputs=[t_delete_armed, t_delete_btn, t_delete_cancel_btn, t_delete_hint],
        )

        t_delete_btn.click(
            fn=topsis_arm_delete,
            inputs=[t_saved_list, t_delete_armed, t_saved_solutions],
            outputs=[t_delete_armed, t_delete_btn, t_delete_cancel_btn, t_delete_hint, t_saved_solutions, t_saved_list, t_history_summary, t_status_message],
        )

        t_delete_cancel_btn.click(
            fn=topsis_cancel_delete,
            outputs=[t_delete_armed, t_delete_btn, t_delete_cancel_btn, t_delete_hint],
        )

        e_solve_outputs = [
            e_conflict_ui, e_pending_request, e_response_output,
            e_kernel_output, e_result_table, e_request_output,
            e_saved_solutions, e_saved_list, e_history_summary, e_status_message,
        ]

        e_saved_solutions.change(
            fn=update_electre_history_summary,
            inputs=e_saved_solutions,
            outputs=e_history_summary,
        )
        e_saved_solutions.change(
            fn=lambda s: gr.update(choices=list(s.keys()) if s else []),
            inputs=e_saved_solutions,
            outputs=e_saved_list,
        )

        app.load(
            fn=initialize_electre_saved_data,
            inputs=[e_saved_solutions],
            outputs=[e_history_summary, e_saved_list],
        )

        e_open_crit_panel_btn.click(fn=show_panel, outputs=e_crit_panel)
        e_cancel_crit_btn.click(fn=hide_panel, outputs=e_crit_panel)
        e_add_crit_btn.click(
            fn=add_electre_criteria,
            inputs=[e_crit_name_input, e_crit_direction_input, e_crit_weight_input, e_crit_type_input, e_criteria_table, e_alternatives_table],
            outputs=[e_criteria_table, e_alternatives_table, e_crit_name_input, e_crit_direction_input, e_crit_weight_input, e_crit_type_input, e_crit_panel],
        )

        e_sync_btn.click(
            fn=sync_electre_alternatives_columns,
            inputs=[e_criteria_table, e_alternatives_table],
            outputs=[e_alternatives_table],
        )

        e_solve_btn.click(
            fn=solve_electre_from_ui,
            inputs=[e_problem_name, e_criteria_table, e_alternatives_table, e_concordance_threshold, e_discordance_threshold, e_saved_solutions],
            outputs=e_solve_outputs,
        )

        e_solve_only_btn.click(
            fn=solve_electre_only,
            inputs=[e_problem_name, e_criteria_table, e_alternatives_table, e_concordance_threshold, e_discordance_threshold],
            outputs=e_solve_outputs,
        )

        e_overwrite_btn.click(
            fn=handle_electre_overwrite,
            inputs=[e_pending_request, e_saved_solutions],
            outputs=e_solve_outputs,
        )

        e_rename_save_btn.click(
            fn=handle_electre_rename,
            inputs=[e_new_name_input, e_pending_request, e_saved_solutions],
            outputs=e_solve_outputs,
        )

        e_saved_list.change(
            fn=load_selected_electre_solution,
            inputs=[e_saved_list, e_saved_solutions],
            outputs=[e_problem_name, e_criteria_table, e_alternatives_table, e_concordance_threshold, e_discordance_threshold, e_response_output, e_saved_request_output, e_saved_response_output, e_kernel_output, e_result_table, e_request_output, e_status_message],
        ).then(
            fn=electre_cancel_delete,
            outputs=[e_delete_armed, e_delete_btn, e_delete_cancel_btn, e_delete_hint],
        )

        e_delete_btn.click(
            fn=electre_arm_delete,
            inputs=[e_saved_list, e_delete_armed, e_saved_solutions],
            outputs=[e_delete_armed, e_delete_btn, e_delete_cancel_btn, e_delete_hint, e_saved_solutions, e_saved_list, e_history_summary, e_status_message],
        )

        e_delete_cancel_btn.click(
            fn=electre_cancel_delete,
            outputs=[e_delete_armed, e_delete_btn, e_delete_cancel_btn, e_delete_hint],
        )

    return app
