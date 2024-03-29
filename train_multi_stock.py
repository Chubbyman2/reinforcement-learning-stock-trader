import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from stable_baselines3 import A2C, PPO
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import DummyVecEnv
from custom_environment_multistock import CustomStockTradingEnv
from data_extractor import get_stock_names


def plot_portfolio(num_shares, stocks, start_date, end_date, name):
    '''
    Given the array of number of shares, plot the amount of each stock
    in the portfolio over time.    
    '''
    plt.figure(figsize=(15, 6))
    num_shares = np.array(num_shares)
    for i in range(num_shares.shape[1]):
        plt.plot(range(num_shares.shape[0]), num_shares[:, i], label=stocks[i])
    plt.title(f"Portfolio Shares, {name}")
    plt.xlabel(f"Day {start_date} - {end_date}")
    plt.ylabel("Number of Shares")
    plt.legend()
    plt.savefig(f"plots/portfolio_shares_{name}.png")
    plt.show()


def train(stocks, start_date, end_date, training_period_length,
          model_name="PPO", features=["Date", "Close", "MACD", "Signal", "RSI", "CCI", "ADX"], 
          window_size=10, k_value=1000, starting_balance=100000, gamma=0.99, num_timesteps=250):
    '''
    This function will train either A2C or PPO using the custom environment created in custom_environment.py.
    The model will be saved and can be loaded later for evaluation.

    Parameters:
    stocks: list of stock tickers (strings)
    start_date: string of start of training period in format "YYYY-MM-DD"
    end_date: string of end of training period in format "YYYY-MM-DD"
    model: string of model to use, either "PPO" or "A2C"
    features: list of features to use, default is what you see
    window_size: int of window size to use, default is 10
    k_value: int of max number of shares to buy/sell at a time
    starting_balance: int of starting balance of account    
    '''
    dfs = [] # Shape (num_stocks, num_days, num_features)
    for stock in stocks:
        # Do not use stocks that do not have enough data
        df = pd.read_csv(f'data/{stock}.csv')
        if len(df) < training_period_length:
            continue
        df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
        df = df[features]
        df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
        df.set_index("Date", inplace=True)
        dfs.append(df)

    env = CustomStockTradingEnv(dfs, window_size=window_size, k=k_value, starting_balance=starting_balance)
    env = DummyVecEnv([lambda: env])
    
    if model_name == "PPO":
        model = PPO("MlpPolicy", env, gamma=gamma, verbose=0)
    elif model_name == "A2C":
        model = A2C("MlpPolicy", env, gamma=gamma, verbose=0)
    else:
        raise ValueError("Please select PPO or A2C")
    # eval_callback = EvalCallback(env, eval_freq=100, n_eval_episodes=5)
    # model.learn(total_timesteps=num_timesteps, callback=[eval_callback])
    model.learn(total_timesteps=num_timesteps)
    
    # Save trained model (this is not the same way you save a Tensorflow model)
    if not os.path.exists("models"):
        os.mkdir("models")
    model.save(f"models/multistock_{model_name}")
    print(f"Model saved as multistock_{model_name}")

    obs = env.reset()
    for i in range(np.array(dfs).shape[1]):
        action, _ = model.predict(obs)
        obs, reward, done, info = env.step(action)
        if done:
            info = info[0]
            account_balances = info['account_balance']
            num_shares = info['num_shares']
            total_portfolio_value = info['total_portfolio_value']
            break

    print("Account balance: {}".format(account_balances[-1]))
    print("Number of shares: {}".format(num_shares[-1]))
    print("Total portfolio value: {}".format(total_portfolio_value[-1]))

    # Plot training results
    plt.figure(figsize=(15, 6))
    plt.plot(total_portfolio_value, label='Portfolio value')
    plt.title(f"Portfolio Value, Multistock")
    plt.xlabel(f"Day {start_date} - {end_date}")
    plt.ylabel("Portfolio Value ($)")

    # Save plot
    if not os.path.exists("plots"):
        os.mkdir("plots")
    plt.savefig(f"plots/training_multistock_{model_name}.png")
    plt.show()


def evaluate(stocks, start_date, end_date, testing_period_length, trained_model, 
             features=["Date", "Close", "MACD", "Signal", "RSI", "CCI", "ADX"], 
             window_size=10, k_value=1000, starting_balance=100000):
    '''
    Load the saved model from the path "trained_model" and evaluate it on the testing data.
    The testing data should be a period of time after the training data that the model has not seen.
    '''
    dfs = []
    for stock in stocks:
        df = pd.read_csv(f'data/{stock}.csv')
        if len(df) < testing_period_length:
            continue
        if end_date is None or end_date == "Present":
            df = df[df["Date"] >= start_date]
            end_date = "Present"
        else:
            df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
        df = df[features]
        df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
        df.set_index("Date", inplace=True)
        dfs.append(df)
    # Create the environment used to test the agent
    env = CustomStockTradingEnv(dfs, window_size=window_size, k=k_value, starting_balance=starting_balance)
    env = DummyVecEnv([lambda: env])
    if trained_model.endswith("PPO"):
        model = PPO.load(trained_model)
    elif trained_model.endswith("A2C"):
        model = A2C.load(trained_model)
    else:
        raise ValueError("Please select PPO or A2C")
    
    # Remember to set random seed for reproducibility
    model.set_random_seed(0)
    
    obs = env.reset()
    for i in range(np.array(dfs).shape[1]):
        action, _ = model.predict(obs)
        obs, reward, done, info = env.step(action)
        if done:
            info = info[0]
            account_balances = info['account_balance']
            num_shares = info['num_shares']
            total_portfolio_value = info['total_portfolio_value']
            break

    # Length is len(df) - window_size = 46
    # print(len(df), len(total_portfolio_value))

    print("Model: {}".format(trained_model))
    print("Account balance: {}".format(account_balances[-1]))
    print("Number of shares: {}".format(num_shares[-1]))
    print("Total portfolio value: {}".format(total_portfolio_value[-1]))

    # Plot testing results
    plt.figure(figsize=(15, 6))
    plt.plot(total_portfolio_value, label='Portfolio value')
    plt.title(f"Portfolio Value, {trained_model[-3:]} Multistock")
    plt.xlabel(f"Day {start_date} - {end_date}")
    plt.ylabel("Portfolio Value ($)")
    plt.savefig(f"plots/testing_multistock_{trained_model.split('_')[-1]}.png")
    plt.show()

    plot_portfolio(num_shares, stocks, start_date, end_date, trained_model[-3:])


def evaluate_both(stocks, start_date, end_date, testing_period_length, trained_model1, trained_model2,
             features=["Date", "Close", "MACD", "Signal", "RSI", "CCI", "ADX"], 
             window_size=10, k_value=1000, starting_balance=100000):
    '''
    Load the saved model from the path "trained_model" and evaluate it on the testing data.
    The testing data should be a period of time after the training data that the model has not seen.
    '''
    dfs = []
    for stock in stocks:
        df = pd.read_csv(f'data/{stock}.csv')
        if len(df) < testing_period_length:
            continue
        if end_date is None or end_date == "Present":
            df = df[df["Date"] >= start_date]
            end_date = "Present"
        else:
            df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
        df = df[features]
        df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
        df.set_index("Date", inplace=True)
        dfs.append(df)

    # Test model 1
    env = CustomStockTradingEnv(dfs, window_size=window_size, k=k_value, starting_balance=starting_balance)
    env = DummyVecEnv([lambda: env])
    if trained_model1.endswith("PPO"):
        model1 = PPO.load(trained_model1)
    elif trained_model1.endswith("A2C"):
        model1 = A2C.load(trained_model1)
    else:
        raise ValueError("Please select PPO or A2C")
    
    # Remember to set random seed for reproducibility
    model1.set_random_seed(0)
    
    obs = env.reset()
    for i in range(np.array(dfs).shape[1]):
        action, _ = model1.predict(obs)
        obs, reward, done, info = env.step(action)
        if done:
            info = info[0]
            account_balances1 = info['account_balance']
            num_shares1 = info['num_shares']
            total_portfolio_value1 = info['total_portfolio_value']
            break
    
    # Test model 2
    env = CustomStockTradingEnv(dfs, window_size=window_size, k=k_value, starting_balance=starting_balance)
    env = DummyVecEnv([lambda: env])
    if trained_model2.endswith("PPO"):
        model2 = PPO.load(trained_model2)
    elif trained_model2.endswith("A2C"):
        model2 = A2C.load(trained_model2)
    else:
        raise ValueError("Please select PPO or A2C")
    
    # Remember to set random seed for reproducibility
    model2.set_random_seed(0)
    
    obs = env.reset()
    for i in range(np.array(dfs).shape[1]):
        action, _ = model2.predict(obs)
        obs, reward, done, info = env.step(action)
        if done:
            info = info[0]
            account_balances2 = info['account_balance']
            num_shares2 = info['num_shares']
            total_portfolio_value2 = info['total_portfolio_value']
            break

    # Plot testing results
    plt.figure(figsize=(15, 6))
    plt.plot(total_portfolio_value1, label='Portfolio Value (A2C)')
    plt.plot(total_portfolio_value2, label='Portfolio Value (PPO)')
    plt.title(f"Portfolio Value, Multistock")
    plt.xlabel(f"Day {start_date} - {end_date}")
    plt.ylabel("Portfolio Value ($)")
    plt.legend(loc="best")
    plt.savefig(f"plots/testing_multistock_ensemble.png")
    plt.show()

if __name__ == "__main__":
    # Training 
    stocks = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL"] 
    # stocks = get_stock_names()
    start_train = "2021-01-01"
    end_train = "2023-01-01"

    # We need to calculate the training period length to cut out stocks that don't have enough data
    # We'll use AAPL as a reference
    df = pd.read_csv(f'data/AAPL.csv')
    df = df[(df["Date"] >= start_train) & (df["Date"] <= end_train)]
    training_period_length = len(df)

    model = "A2C"
    features = ["Date", "Close", "MACD", "Signal", "RSI", "CCI", "ADX"]
    window_size = 10
    k_value = 100 / (2 * len(stocks))
    starting_balance = 100000
    gamma = 0.95
    num_timesteps = 250
    train(stocks, start_train, end_train, training_period_length, model, features, window_size, k_value, starting_balance, gamma, num_timesteps)

    model = "PPO"
    train(stocks, start_train, end_train, training_period_length, model, features, window_size, k_value, starting_balance, gamma, num_timesteps)

    # Evaluation
    start_test = "2023-01-01"
    end_test = None
    df = pd.read_csv(f'data/AAPL.csv')
    if end_test is None or end_test == "Present":
        df = df[df["Date"] >= start_test]
        end_test = "Present"
    else:
        df = df[(df["Date"] >= start_test) & (df["Date"] <= end_test)]
    testing_period_length = len(df)
    trained_model = f"models/multistock_A2C"
    evaluate(stocks, start_test, end_test, testing_period_length, trained_model, features, window_size, k_value, starting_balance)
    
    trained_model = f"models/multistock_PPO"
    evaluate(stocks, start_test, end_test, testing_period_length, trained_model, features, window_size, k_value, starting_balance)

    # Ensemble
    trained_model1 = f"models/multistock_A2C"
    trained_model2 = f"models/multistock_PPO"
    evaluate_both(stocks, start_test, end_test, testing_period_length, trained_model1, trained_model2, features, window_size, k_value, starting_balance)