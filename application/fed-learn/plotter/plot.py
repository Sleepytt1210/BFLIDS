import numpy as np
import matplotlib.pyplot as plt
import os.path as path

def parse_histories(histories: dict):
    res = {}
    for history in histories:
        loss = np.array(history.losses_distributed)[:, -1]
        if 'loss' not in res.keys():
            res['loss'] = []
        res['loss'].append(loss)
        for metric_name, vals in history.metrics_distributed.items():
            metric_vals = np.array(vals)[:, -1]
            if metric_name not in res.keys():
                res[metric_name] = []
            res[metric_name].append(metric_vals)
    return res

def plot_all(histories, num_rounds, suffix='actual_run_1'):
    flattened_histories = parse_histories(histories)
    for metric_name, history in flattened_histories.items():
        plt.figure(metric_name)
        plt.title(f"{metric_name.title()} of each FL session over {num_rounds} rounds")
        isLoss = metric_name == 'loss'
        history = np.array(history) * 100 if not isLoss else np.array(history)
        max_val = np.amax(history)
        min_val = np.amin(history)
        rmk_val = max_val if not isLoss else min_val
        ori_idx = history.argmax() if not isLoss else history.argmin()
        rmk_idx = np.unravel_index(ori_idx, history.shape)
        for run, vals in enumerate(history):
            plt.plot(vals, label=f"Session {run}")

        y_offset = (max_val - min_val) * 0.1
        plt.annotate(f'{"Max" if not isLoss else "Min"} {metric_name.lower()}[Session {rmk_idx[0]}]: ({rmk_val:.2f}{"%" if not isLoss else ""})',
                     xy=(rmk_idx[1], rmk_val), 
                     xytext=(rmk_idx[1] - 10, rmk_val + y_offset if isLoss else rmk_val - y_offset),
                     arrowprops=dict(arrowstyle='->', lw=1))
        plt.legend()
        plt.ylabel(f"{metric_name.lower()}{' (%)' if not isLoss else ''}")
        plt.xlabel('round')
        plt.grid()
        plt.savefig(path.abspath(f"./plotter/figures/{metric_name.lower()}_{suffix}.png"))

def plot_time(times, runs, suffix='actual_run_1'):
    plt.figure('timetaken')
    plt.title("Time taken for each run of federated learning session (s)")
    avg = sum(times)/runs
    max_t = max(times)
    r = np.argmax(times) # Round number of the maximum
    plt.plot(times, label='time taken')
    plt.plot(np.full(shape=len(times), fill_value=(sum(times)/runs)), label=f'average time ({avg:.2f}s)')
    plt.annotate(f'Max time ({max_t:.2f}s)', xy=(r, max_t), xytext=(r+1, max_t-50), arrowprops=dict(arrowstyle='->', lw=1))
    plt.xlabel('session')
    plt.ylabel('time (s)')
    plt.legend()
    plt.grid()
    plt.savefig(path.abspath(f"./plotter/figures/time_taken_{suffix}.png"))


if __name__ == '__main__':
    import pickle
    with open(path.abspath('./plotter/histories/hist_2'), 'rb') as f:
        histories = pickle.load(f)        
        # times = np.array([history.elapsed for history in histories])
        # plot_time(times, 10)
        # plot_all(histories, 30, 'sim_only')
        metric_name = 'accuracy'
        history = parse_histories(histories)['accuracy']
        num_rounds = 30
        plt.figure(metric_name)
        plt.title(f"{metric_name.title()} of each FL session over {num_rounds} rounds")
        isLoss = metric_name == 'loss'
        history = np.array(history) * 100 if not isLoss else np.array(history)
        max_val = np.amax(history)
        min_val = np.amin(history)
        rmk_val = max_val if not isLoss else min_val
        ori_idx = history.argmax() if not isLoss else history.argmin()
        rmk_idx = np.unravel_index(ori_idx, history.shape)
        for run, vals in enumerate(history):
            plt.plot(vals, label=f"Session {run}")

        y_offset = (max_val - min_val) * 0.17
        plt.annotate(f'{"Max" if not isLoss else "Min"} {metric_name.lower()}[Session {rmk_idx[0]}]: ({rmk_val:.2f}{"%" if not isLoss else ""})',
                     xy=(rmk_idx[1], rmk_val), 
                     xytext=(rmk_idx[1] - 10, rmk_val + y_offset if isLoss else rmk_val - y_offset),
                     arrowprops=dict(arrowstyle='->', lw=1))
        plt.legend()
        plt.ylabel(f"{metric_name.lower()}{' (%)' if not isLoss else ''}")
        plt.xlabel('round')
        plt.grid()
        plt.savefig(path.abspath(f"./plotter/figures/{metric_name.lower()}_actual_run_1.png"))