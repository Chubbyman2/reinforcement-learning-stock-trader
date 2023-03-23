# reinforcement-learning-stock-trader
<img src="https://compote.slate.com/images/926e5009-c10a-48fe-b90e-fa0760f82fcd.png?width=1200&rect=680x453&offset=0x30">

## Prerequisites
All code was written in Python 3.10. Please see <a href="https://github.com/Chubbyman2/reinforcement-learning-stock-trader/blob/main/requirements.txt">requirements.txt</a> for dependencies.
```
pandas-datareader==0.10.0
scipy==1.10.1
tensorflow==2.11.0
tqdm==4.65.0
yfinance==0.2.12
```

## Description of Files
### <a href="https://github.com/Chubbyman2/reinforcement-learning-stock-trader/blob/main/data_extractor.py">data_extractor.py</a>
This file contains all the code used to extract the list of stocks on the S&P 500 and their respective financial data. It also contains a dataloader function for loading the correct data in the training scripts. See doc strings for details.

### <a href="https://github.com/Chubbyman2/reinforcement-learning-stock-trader/blob/main/single_feature_model.py">single_feature_model.py</a> and <a href="https://github.com/Chubbyman2/reinforcement-learning-stock-trader/blob/main/multi_feature_model.py">multi_feature_model.py</a>
This is where the deep Q-learning models are defined, along with the trade and batch_train methods used in the training scripts. The single feature model only takes in the closing price as a feature, while the multi-feature model takes in as many features as is defined in the training script. Modifications were made accordingly to the multi-feature model methods.

### <a href="https://github.com/Chubbyman2/reinforcement-learning-stock-trader/blob/main/train_single_feature.py">train_single_feature.py</a> and <a href="https://github.com/Chubbyman2/reinforcement-learning-stock-trader/blob/main/train_multi_feature.py">train_multi_feature.py</a>
This is where the training for the model actually happens. Note that for the multi-feature model's training, we defined the function to allow for multiple stocks to be used, as a further improvement on the single-feature training.

## License
This project is licensed under the MIT License - see the <a href="https://github.com/Chubbyman2/reinforcement-learning-stock-trader/blob/main/LICENSE">LICENSE</a> file for details.
