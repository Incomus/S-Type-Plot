import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
pd.set_option('display.max_rows', None)

def summarize_folders(main_folder_path):
    variable_count, variation_count, experiment_count = 0, 0, 0
    main_folder = Path(main_folder_path)
    
    for param_folder in main_folder.iterdir():
        if param_folder.is_dir():
            variable_count += 1
            for variation_folder in param_folder.iterdir():
                if variation_folder.is_dir():
                    variation_count += 1
                    experiment_count += sum(1 for _ in variation_folder.glob("*.xlsx"))
    
    print(f'Found {variable_count} variable parameters, {variation_count} variable variations, {experiment_count} experiments')

def choose(text, *options):
    options = list(options)  # Convert the tuple to a list for easier handling
    while (user_input := input(f'{text}\n({"/".join(options)})\n')) not in options:
        print('Invalid input\n')
    return user_input

    
# Prompt for settings
def get_user_setup():
    if choose('Choose operation:\n1 - Default\n2 - Phase response time', '1', '2') == '1':
        if choose('Change default settings?', 'y', 'n') == 'y':
            ignore_primary = choose('Ignore first variable?', 'y', 'n')
            ignore_secondary = choose('Ignore second variable?', 'y', 'n')
            ignore_diff = choose('Ignore difference?', 'y', 'n') if ignore_secondary == 'n' else 'y'
            def_state = '1'
        else:
            def_state, ignore_primary, ignore_secondary, ignore_diff = '1', 'n', 'n', 'n'
    else:
        def_state, ignore_primary, ignore_secondary, ignore_diff = '2', 'n', 'n', 'n'
    return def_state, ignore_primary, ignore_secondary, ignore_diff

def process_files(main_folder_path, def_state, ignore_primary, ignore_secondary):
    data, failed_files = [], []
    main_folder = Path(main_folder_path)
    count = 0
    for param_folder in main_folder.iterdir():
        for variation_folder in param_folder.iterdir():
            if variation_folder.is_dir():
                for file in variation_folder.glob("*.xlsx"):
                    try:
                        df = pd.read_excel(file)
                        df.columns = df.columns.str.lower().str.replace(" ", "_")
                        if def_state == '2':
                            file = file.stem.replace("Response_Time", "Response Time").replace("TFall_", "TFall ").replace("TRise_", "TRise ")
                            df = df.iloc[:, 1:3]
                        else:
                            file = file.stem
                            df = df.iloc[:, :2]  # Keep only first two columns

                        #print('1')
                        #print(file)
                        #print('2')
                        #print(file)
                        variables = file.split('_')
                        for i, var in enumerate(variables):
                            df[f'variable{i+1}'] = var

                        df['id'] = count
                        count += 1
                        df['main_parameter'] = variation_folder.name
                        df['param_name'] = param_folder.name
                        data.append(df)
                    except Exception as e:
                        failed_files.append((file, str(e)))

    if data:
        final_df = pd.concat(data, ignore_index=True)
        #print(final_df.columns)
        #print(final_df)
        final_df.columns = ['x', 'y', 'name', 'type', 'exp_n', 'primary', 'measurable', 'secondary', 'date', 'time', 'id', 'main_parameter', 'param_name']
        final_df.drop(columns=['name', 'type', 'measurable', 'date', 'time'], inplace=True)
    else:
        print("No valid data found.")
        return pd.DataFrame(), failed_files
    
    if ignore_primary == 'y':
        final_df['primary'] = ''
    if ignore_secondary == 'y':
        final_df['secondary'] = ''
    
    return final_df, failed_files

def calculate_r2(final_df, ignore_primary, ignore_secondary, ignore_diff):
    if final_df.empty:
        return
    
    unique_params = final_df['main_parameter'].unique()
    unique_primarys = final_df['primary'].unique()
    unique_secondarys = final_df['secondary'].unique()

    final_df['R2'] = None
    final_df['avg_y'] = None
    for main_parameter in unique_params:
        for primary in unique_primarys:
            for secondary in unique_secondarys:
                filtered_df = final_df[(final_df['primary'] == primary) & (final_df['secondary'] == secondary) & (final_df['main_parameter'] == main_parameter)]
                grouped = filtered_df.groupby(['param_name', 'main_parameter', 'primary', 'secondary', 'x'])['y'].mean().reset_index()
                grouped.rename(columns={'y': 'avg'}, inplace=True)

                for exp in filtered_df['exp_n'].unique():
                    exp_df = filtered_df[filtered_df['exp_n'] == exp].reset_index(drop=True)

                    # Merge exp_df with grouped by matching on 'param_name' and 'x'
                    exp_merged = pd.merge(exp_df, grouped, on=['param_name', 'main_parameter', 'primary', 'secondary', 'x'], how='left')

                    # Calculate SS_res and SS_tot
                    ss_res = (exp_merged['avg'] - exp_merged['y']) ** 2
                    ss_tot = (exp_merged['y'] - exp_merged['y'].mean()) ** 2
                    # Calculate R² value
                    r2_value = 1 - ss_res.sum() / ss_tot.sum()
                    
                    # Update final_df with the R² value
                    final_df.loc[(final_df['primary'] == primary) & (final_df['secondary'] == secondary) & 
                                 (final_df['exp_n'] == exp) & (final_df['main_parameter'] == main_parameter), 'R2'] = r2_value
                    final_df.loc[(final_df['primary'] == primary) & (final_df['secondary'] == secondary) & 
                                 (final_df['exp_n'] == exp) & (final_df['main_parameter'] == main_parameter), 'avg_y'] = exp_merged['y'].mean()
    return final_df
        
def final_plot(final_df):
    unique_primarys = final_df['primary'].unique()
    unique_secondarys = final_df['secondary'].unique()
    param_name = final_df['param_name'][0]
    
    grouped = final_df.groupby(['param_name', 'main_parameter', 'primary', 'secondary', 'x'])['y'].mean().reset_index()
    grouped = grouped.rename(columns={'y': 'avg_y'})
    
    # Define the grid size for subplots based on the number of unique primary and secondary combinations
    measurable = final_df.columns[1]
    values = final_df.columns[0]
    n_rows = len(unique_primarys)
    n_cols = len(unique_secondarys) + 1
    if len(unique_secondarys) == 1:
        cols_1 = True
    else:
        cols_1 = False
        
    if n_rows == 1:
        n_rows += 1
        rows_1 = True
    else:
        rows_1 = False
    
    fig, axes = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=(n_cols * 5, n_rows * 5))
    # Loop through combinations of primary and secondary to draw s/v plots
    for s_idx, primary in enumerate(unique_primarys):  # Loop over rows (unique_primarys)
        for v_idx, secondary in enumerate(unique_secondarys):  # Loop over columns (unique_secondarys)

            # Filter data for the current combination of primary and secondary
            filtered_df = grouped[(grouped['primary'] == primary) & (grouped['secondary'] == secondary)]
            
            # Get unique main_parameters
            main_parameters = filtered_df['main_parameter'].unique()
            
            # Plot for each main_parameter in the respective subplot
            #print(n_rows, n_cols)
            #print(s_idx, v_idx)
            #print(axes)
            ax = axes[s_idx, v_idx]  # Access the subplot in the column for the current secondary and row for primary
            param_legend = 'R2av:'
            for param in main_parameters:
                r2_mean = final_df.loc[
                    (final_df['primary'] == primary) & 
                    (final_df['secondary'] == secondary) & 
                    (final_df['main_parameter'] == param),
                    ['R2']
                ].mean()
                r2_mean = round(pd.to_numeric(r2_mean.values[0]), 3)
                param_legend += str(param) + '=' + str(r2_mean) + ';'
                param_df = filtered_df[filtered_df['main_parameter'] == param]
                ax.plot(param_df['x'], param_df['avg_y'], label=f'{param}')
            
            # Set titles and labels for each subplot
            ax.set_xlabel(values)
            ax.set_ylabel(measurable)
            if ignore_primary != 'y' and ignore_secondary != 'y':
                legend_set = f'{primary}, {secondary}\n{param_legend}'
            elif ignore_primary != 'y':
                legend_set = f'{primary}\n{param_legend}'
            elif ignore_secondary != 'y':
                legend_set = f'{secondary}\n{param_legend}'
            else:
                legend_set = param_legend
            ax.set_title(legend_set, fontsize=8)
            ax.legend(title=param_name)
            ax.grid(True)
    
    # Plotting the secondary differences in the last column of each row
    if len(unique_secondarys) > 1 and ignore_diff != 'y':
        # Calculating the index for secondary difference column (last column in each row)
        secondary_diff = grouped.pivot_table(index=['main_parameter', 'primary', 'x'], columns='secondary', values='avg_y')
        secondary_diff = secondary_diff.reset_index()
        secondary_diff['secondary_diff'] = secondary_diff[secondary_diff.columns[-len(unique_secondarys)]] - secondary_diff[secondary_diff.columns[-1]]

        for s_idx, primary in enumerate(unique_primarys):
            primary_df = secondary_diff[secondary_diff['primary'] == primary]
            ax = axes[s_idx, -1]  # Access the last column in the row
            
            for param in main_parameters:
                param_df = primary_df[primary_df['main_parameter'] == param]
                ax.plot(param_df['x'], param_df['secondary_diff'], label=f'{param}')
            
            # Set titles and labels for the secondary difference subplots
            ax.set_xlabel(values)
            ax.set_ylabel(measurable)
            if ignore_primary != 'y':
                legend_set = f'{primary}, {secondary_diff.columns[-len(unique_secondarys)-1]} - {secondary_diff.columns[-2]}'
            else:
                legend_set = f'{secondary_diff.columns[-len(unique_secondarys)-1]} - {secondary_diff.columns[-2]}'
            ax.set_title(legend_set)
            ax.legend(title=param_name)
            ax.grid(True)

    # Adjust layout so that subplots don't overlap
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.15, hspace=0.35)
    
    # Display R² summary
    r2_summary = final_df.drop(columns=['x', 'y']).drop_duplicates().reset_index(drop=True)
    r2_summary['R2'] = pd.to_numeric(r2_summary['R2'], errors='coerce')
    r2_summary['R2'] = round(r2_summary['R2'], 3)
    r2_summary = r2_summary.sort_values(by=['main_parameter', 'primary', 'secondary', 'exp_n']).reset_index(drop=True)
    print('\nMain parameter: ' + param_name)
    print(r2_summary)
    print()

    # Display the figure
    if rows_1:
        for ax in axes[-1, :]:
            ax.remove() 
    if cols_1:
        if rows_1:
            axes[0][-1].remove()
        else:
            for ax in axes[:, -1]:
                ax.remove() 
    else:
        if ignore_diff == 'y':
            if rows_1:
                axes[0][-1].remove()
            else:
                for ax in axes[:, -1]:
                    ax.remove() 
            
    plt.show()
        
def calculate_t(final_df):
    if final_df.empty:
        return
    
    unique_params = final_df['main_parameter'].unique()
    unique_secondarys = final_df['secondary'].unique()

    final_df['time'] = None
    final_df['phase'] = None
    
    for main_parameter in unique_params:
        for secondary in unique_secondarys:
            filtered_df = final_df[(final_df['secondary'] == secondary) & (final_df['main_parameter'] == main_parameter)]

            for id in filtered_df['id'].unique():
                exp_df = filtered_df[filtered_df['id'] == id].reset_index(drop=True)
                
                y_max_idx = exp_df['y'].abs().idxmax()
                y_max = exp_df['y'].iloc[y_max_idx]
                
                y_10 = exp_df['y'].min() + 0.1 * (exp_df['y'].max() - exp_df['y'].min())
                y_90 = exp_df['y'].min() + 0.9 * (exp_df['y'].max() - exp_df['y'].min())
                    
                row_10 = exp_df.iloc[(exp_df['y'] - y_10).abs().idxmin()]
                row_90 = exp_df.iloc[(exp_df['y'] - y_90).abs().idxmin()]
                
                x_10 = row_10['x']
                x_90 = row_90['x']
                x_dx = abs(x_90 - x_10)
                
                # Update final_df with the R² value
                final_df.loc[(final_df['secondary'] == secondary) & 
                             (final_df['id'] == id) & (final_df['main_parameter'] == main_parameter), 'phase'] = y_max
                final_df.loc[(final_df['secondary'] == secondary) & 
                             (final_df['id'] == id) & (final_df['main_parameter'] == main_parameter), 'time'] = x_dx
    final_df = final_df.drop(columns=['x', 'y']).drop_duplicates().reset_index(drop=True)
    for col in ['phase', 'time']:
        final_df[col] = pd.to_numeric(final_df[col], errors='coerce').round(3)

    final_df = final_df.sort_values(by=['main_parameter', 'secondary', 'exp_n', 'id']).reset_index(drop=True)
    
    param_name = final_df['param_name'][0]
    final_df = final_df.drop(columns=['primary', 'param_name']).drop_duplicates().reset_index(drop=True)
    final_df = final_df.rename(columns={'secondary': 'time_type'})
    final_df = final_df.reindex(columns = ['id', 'exp_n', 'main_parameter', 'time_type', 'time', 'phase'])
    print('\nMain parameter: ' + param_name)
    for type in final_df['time_type'].unique():
        print(final_df[final_df['time_type'] == type])
        print()

# Main execution
if __name__ == "__main__":
    # Instructions for creating folder structure and adding test data
    print("""
    How to:
    1. Create a folder with the parameter name you want to test.
    2. Inside that folder, create subfolders for each variation of the parameter (e.g., gap with 50, 75, and 100 μm).
    3. Place the WNA Excel test data for S11/S12 (y) in the respective folders.
    4. The program expects filenames in the following format, where each part is separated by an underscore:
       'JNC Heights 01-07-24_Phase Shifter_15 r_S11_y_0V_2024-07-02_12-47-17'
       This format is interpreted as: name (not used), type (not used), experiment number, primary, measurable, secondary, date (not used), time (not used).
       
    """)
    
    main_folder_path = input("Input path to the main folder:\n")
    summarize_folders(main_folder_path)
    def_state, ignore_primary, ignore_secondary, ignore_diff = get_user_setup()

    final_df, failed_files = process_files(main_folder_path, def_state, ignore_primary, ignore_secondary)
    if failed_files:
        print("Failed to process the following files:")
        for file, error in failed_files:
            print(f"{file}: {error}")
    
    for param_name in final_df['param_name'].unique():
        final_df_0 = final_df[final_df['param_name'] == param_name].reset_index(drop=True)
        if def_state == '1':
                final_df_0 = calculate_r2(final_df_0, ignore_primary, ignore_secondary, ignore_diff)
                final_plot(final_df_0)
        else:
            calculate_t(final_df_0)
    input("Press Enter to exit\n")
