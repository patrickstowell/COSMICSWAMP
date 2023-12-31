
from pcse.db import NASAPowerWeatherDataProvider
import datetime
import pandas as pd
import matplotlib.pyplot as plt

import warnings
import itertools
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
import matplotlib
import pmdarima as pm

longitude = -45.523917847717236
latitude = -12.170341419421398


wdp = NASAPowerWeatherDataProvider(longitude=longitude, latitude=latitude)

start_date=pd.to_datetime("2023-01-01").date()
end_date=pd.to_datetime("2025-12-01").date()

pre_date = (pd.to_datetime(start_date) - datetime.timedelta(days=365*10)).date()
print(pre_date)

dataset = {
    "Date":   [],
    "IRRAD": [],
    "TMIN":  [],
    "TMAX":  [],
    "VAP":   [],
    "RAIN":  [],
    "E0":    [],
    "ES0":   [],
    "ET0":   [],
    "WIND":  [],
    "TEMP":  []
}

while pre_date < start_date:
    print(pre_date)
    pre_date += datetime.timedelta(days=1)

    vals = wdp(pre_date)
    print(vals, pre_date)

    dataset["Date"].append(pre_date)
    dataset["IRRAD"].append( vals.IRRAD )
    dataset["TMIN"].append( vals.TMIN )
    dataset["TMAX"].append( vals.TMAX )
    dataset["VAP"].append( vals.VAP )
    dataset["RAIN"].append( vals.RAIN )
    dataset["E0"].append( vals.E0 )
    dataset["ES0"].append( vals.ES0 )
    dataset["ET0"].append( vals.ET0 )
    dataset["WIND"].append( vals.WIND )
    dataset["TEMP"].append( vals.TEMP )

df = pd.DataFrame(data=dataset)

for key in df:
    if "Date" in key: continue
    df[key+"_mean"] = df[key].mean()
    df[key] /= df[key+"_mean"]

df.isnull().sum()
df = df.dropna()
df.isnull().sum()

df['Date'] = pd.to_datetime(df['Date'])
df["Month"] = pd.PeriodIndex(df['Date'], freq="W")

df = df.groupby("Month").mean().reset_index()
df = df.set_index("Date")
df = df.drop("Month", axis=1)

for key in df:
    if key == "Month": continue
    if "mean" in key: continue
    decomposition = sm.tsa.seasonal_decompose(df[key], period=52, model="additive")
    
    # fig = decomposition.plot()
    # plt.show()

    df[key+"_trend"] = decomposition.trend
    df[key+"_seasonal"] = decomposition.seasonal
    df[key+"_residual"] = decomposition.resid


df = df.resample('D')
df = df.interpolate(method='linear', fill_value=0.0)
df["day_of_year"] = pd.to_datetime(df.index).day_of_year
sdf = df.groupby(["day_of_year"]).mean()


print(sdf)


forecast_rows = {
    "Date": [],
    "IRRAD": [],
}

current_date = start_date
while current_date < end_date:
    current_date += datetime.timedelta(days=1)
    current_day_of_year = pd.to_datetime(current_date).day_of_year
    row = sdf.loc[current_day_of_year]

    forecast_rows["Date"].append(current_date)
    forecast_rows["IRRAD"].append((row.IRRAD_seasonal + row.IRRAD_trend)*row.IRRAD_mean)


forecast_df = pd.DataFrame(data=forecast_rows)
print(forecast_df)

plt.scatter(df.index, df.IRRAD*df.IRRAD_mean, s=3)
plt.plot(df.index, (df.IRRAD_seasonal + df.IRRAD_trend)*df.IRRAD_mean)
plt.plot(forecast_df.Date, forecast_df.IRRAD)

plt.show()


# interpolated = pd.to_datetime(interpolated.index).day_of_year
# print("SEASON", interpolated["day_of_year"])
# interpolated.reset_index()
# print(interpolated)

# seasonal_estimate = interpolated.groupby(["day_of_year"])
# plt.plot(seasonal_estimate.index, seasonal_estimate)
# plt.show()
# train = df.TMIN[0:int(len(df)*0.9)]
# valid = df.TMIN[int(len(df)*0.9):-1]




# # ax = seasonal.plot(label='Seasonality', color='blue')
# # min_ = seasonal.idxmin()
# # max_ = seasonal.idxmax()
# # min_2 = seasonal[max_:].idxmin()
# # max_2 = seasonal[min_2:].idxmax()
# # ax.axvline(min_,label='min 1',c='red')
# # ax.axvline(min_2,label='min 2',c='red', ls=':')
# # ax.axvline(max_,label='max 1',c='green')
# # ax.axvline(max_2,label='max 2',c='green', ls=':')
# # plt.legend(loc='upper right', fontsize='x-small')
# # print(f'The time difference between the two minimums is {min_2-min_}')
# # plt.show()


# # from statsmodels.tsa.stattools import adfuller

# # ts_month_avg = df
# # def adf_test(timeseries):
# #     #Perform Dickey-Fuller test:
# #     print ('Results of Dickey-Fuller Test:')
# #     dftest = adfuller(timeseries, autolag='AIC')
# #     dfoutput = pd.Series(dftest[0:4], index=['Test Statistic','p-value','#Lags Used','Number of Observations Used'])
# #     for key,value in dftest[4].items():
# #        dfoutput['Critical Value (%s)'%key] = value
# #     print (dfoutput)

# # print(adf_test(ts_month_avg))

# # ts_t_adj = ts_month_avg - ts_month_avg.shift(1)
# # ts_t_adj = ts_t_adj.dropna()
# # ts_t_adj.plot()

# # print(adf_test(ts_month_avg))

# # ts_s_adj = ts_t_adj - ts_t_adj.shift(365)
# # ts_s_adj = ts_s_adj.dropna()
# # ts_s_adj.plot()

# # print(adf_test(ts_month_avg))

# # from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
# # plot_acf(ts_s_adj)
# # matplotlib.pyplot.show()
# # plot_pacf(ts_s_adj)
# # matplotlib.pyplot.show()


# # p = range(0, 3)
# # d = range(1,2)
# # q = range(0, 3)
# # pdq = list(itertools.product(p, d, q))
# # seasonal_pdq = [(x[0], x[1], x[2], 12) for x in list(itertools.product(p, d, q))]
# # print('Examples of parameter combinations for Seasonal ARIMA...')
# # print('SARIMAX: {} x {}'.format(pdq[1], seasonal_pdq[1]))
# # print('SARIMAX: {} x {}'.format(pdq[1], seasonal_pdq[2]))
# # print('SARIMAX: {} x {}'.format(pdq[2], seasonal_pdq[3]))
# # print('SARIMAX: {} x {}'.format(pdq[2], seasonal_pdq[4]))

# # for param in pdq:
# #     for param_seasonal in seasonal_pdq:
# #         try:
# #             mod = sm.tsa.statespace.SARIMAX(y,
# #                                             order=param,
# #                                             seasonal_order=param_seasonal,
# #                                             enforce_stationarity=False,
# #                                             enforce_invertibility=False)
# #             results = mod.fit()
# #             print('ARIMA{}x{}12 - AIC:{}'.format(param, param_seasonal, results.aic))
# #         except:
# #             continue


# # y_forecasted = pred.predicted_mean
# # y_truth = ts_s_adj['2019-01-01':]
# # mse = ((y_forecasted - y_truth) ** 2).mean()
# # print('The Mean Squared Error is {}'.format(round(mse, 2)))
# # print('The Root Mean Squared Error is {}'.format(round(np.sqrt(mse), 2)))

# # print(df)

# # plt.plot(df.DAY, df.E0)
# # plt.show()

# # ntrain = int(0.9*len(df))
# # nvalid = int(0.1*len(df))
# # valid = df.TMIN.tail(nvalid)
# # train = df.TMIN.head(ntrain)

# # from pmdarima.model_selection import train_test_split
# # #Train/Test split
# # train, test = train_test_split(seasonal, train_size=int(len(df)*0.75))


# # # #building the model
# # from pmdarima import auto_arima
# # # model = auto_arima(train, trace=True, error_action='ignore', suppress_warnings=True, m=366)
# # model = pm.auto_arima(y=train, start_p=0, start_q=0, max_p=5,
# #                            max_q=5, start_P=0, start_Q=0, max_P=5,
# #                            max_Q=5, m=52, max_order=None, seasonal=True,
# #                            trace=True)

# # model.fit(train)

# # # display(model.summary())
# # # model.plot_diagnostics(figsize=(12,6));

# # forecast = model.predict(n_periods=len(test))
# # print("ARIMA forecast", forecast.values)
# # forecast = pd.DataFrame({"Date": test.index, "TMIN": forecast.values})
# # forecast = forecast.set_index("Date")
# # print(forecast)

# # # forecast = forecast.resample('D').interpolate()
# # # test = test.resample('D').interpolate()

# # print(forecast)
# # #plot the predictions for testation set
# # # plt.plot(train, label='Train')
# # plt.plot(train, label='Train')
# # plt.plot(test, label='Valid')
# # plt.plot(forecast, label='Prediction')
# # plt.show()


# # # Author: Taylor Smith <taylor.smith@alkaline-ml.com>

# # import pmdarima as pm
# # from pmdarima import model_selection
# # from sklearn.metrics import mean_squared_error
# # import matplotlib.pyplot as plt
# # import numpy as np

# # # #############################################################################
# # # Load the data and split it into separate pieces
# # data = pm.datasets.load_lynx()
# # train, test = model_selection.train_test_split(data, train_size=90)

# # print(data, train, test)
# # # Fit a simple auto_arima model
# # modl = pm.auto_arima(train, start_p=1, start_q=1, start_P=1, start_Q=1,
# #                      max_p=5, max_q=5, max_P=5, max_Q=5, seasonal=True,
# #                      stepwise=True, suppress_warnings=True, D=10, max_D=10,
# #                      error_action='ignore')

# # # Create predictions for the future, evaluate on test
# # preds, conf_int = modl.predict(n_periods=test.shape[0], return_conf_int=True)

# # # Print the error:
# # print("Test RMSE: %.3f" % np.sqrt(mean_squared_error(test, preds)))

# # # #############################################################################
# # # Plot the points and the forecasts
# # x_axis = np.arange(train.shape[0] + preds.shape[0])
# # x_years = x_axis + 1821  # Year starts at 1821

# # plt.plot(x_years[x_axis[:train.shape[0]]], train, alpha=0.75)
# # plt.plot(x_years[x_axis[train.shape[0]:]], preds, alpha=0.75)  # Forecasts
# # plt.scatter(x_years[x_axis[train.shape[0]:]], test,
# #             alpha=0.4, marker='x')  # Test data
# # plt.fill_between(x_years[x_axis[-preds.shape[0]:]],
# #                  conf_int[:, 0], conf_int[:, 1],
# #                  alpha=0.1, color='b')
# # plt.title("Lynx forecasts")
# # plt.xlabel("Year")
# # plt.show()


# # """
# # =======================
# # Simple auto_arima model
# # =======================


# # This is a simple example of how we can fit an ARIMA model in several lines
# # without knowing anything about our data or optimal hyper parameters.

# # .. raw:: html

# #    <br/>
# # """
# # print(__doc__)

# # # Author: Taylor Smith <taylor.smith@alkaline-ml.com>

# # import pmdarima as pm
# # from pmdarima import model_selection
# # import numpy as np
# # from matplotlib import pyplot as plt

# # # #############################################################################
# # # Load the data and split it into separate pieces
# # data = pm.datasets.load_wineind()
# # print(data)
# # data = df.TMAX.values
# # train, test = model_selection.train_test_split(data, train_size=150)

# # # Fit a simple auto_arima model
# # # arima = pm.auto_arima(train, error_action='ignore', trace=True,
# # #                       suppress_warnings=True, maxiter=5,
# # #                       seasonal=True, m=12)

# # from pmdarima.arima import ndiffs

# # kpss_diffs = ndiffs(train, alpha=0.05, test='kpss', max_d=365)
# # adf_diffs = ndiffs(train, alpha=0.05, test='adf', max_d=365)
# # n_diffs = max(adf_diffs, kpss_diffs)

# # arima = pm.auto_arima(train, d=n_diffs, seasonal=False, stepwise=True,
# #                      suppress_warnings=True, error_action="ignore", max_p=365,
# #                      max_order=None, trace=True)

# # from sklearn.metrics import mean_squared_error
# # from pmdarima.metrics import smape

# # model = arima

# # def forecast_one_step():
# #     fc, conf_int = model.predict(n_periods=1, return_conf_int=True)
# #     return (
# #         fc.tolist()[0],
# #         np.asarray(conf_int).tolist()[0])

# # forecasts = []
# # confidence_intervals = []

# # for new_ob in test:
# #     fc, conf = forecast_one_step()
# #     forecasts.append(fc)
# #     confidence_intervals.append(conf)
    
# #     # Updates the existing model with a small number of MLE steps
# #     model.update(new_ob)
    
# # print(f"Mean squared error: {mean_squared_error(test, forecasts)}")
# # print(f"SMAPE: {smape(test, forecasts)}")

# # x = np.arange(test.shape[0])
# # plt.scatter(x, test, marker='x')
# # plt.plot(x, model.predict(n_periods=test.shape[0]))
# # plt.title('Actual test samples vs. forecasts')
# # plt.show()


# # # # #############################################################################
# # # # Plot actual test vs. forecasts:
# # # x = np.arange(test.shape[0])
# # # plt.scatter(x, test, marker='x')
# # # plt.plot(x, arima.predict(n_periods=test.shape[0]))
# # # plt.title('Actual test samples vs. forecasts')
# # # plt.show()

