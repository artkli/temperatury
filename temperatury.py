import datetime
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D


# zaokraglenie czasu do wartosci round_to w dol
def round_time(dt, round_to=300):
    seconds = (dt.replace(tzinfo=None) - dt.min).seconds
    rounding = seconds // round_to * round_to
    return dt + datetime.timedelta(0, rounding-seconds, -dt.microsecond)


# zwraca wartosc wiersza i kolumny na podstawie numeru kolejnej danej
def item_to_coordinate(item, rows):
    return item // rows, item % rows


# ilosc pomiarów w dniu (co 5 minut)
ROWS = STEPS = 288
# brak danych
NV = -273.15

# wczytanie danych wygenerowanych przez Raspberry PI
FILENAME = 'dane\\outer.csv'
read_data = pd.read_csv(FILENAME, sep='[ ;]', decimal=',', names=['date', 'time', 'temp'], engine='python')

# obliczenie ilosci wczytanych dni
first_date = datetime.datetime.strptime(read_data.iloc[0]['date'], '%d.%m.%Y')
last_date = datetime.datetime.strptime(read_data.iloc[-1]['date'], '%d.%m.%Y')
COLUMNS = DAYS = (last_date - first_date).days + 1
LEN = ROWS*COLUMNS

# zainicjowanie macierzy danych
first_date_str = np.datetime64(datetime.datetime.strptime(read_data.iloc[0]['date'], '%d.%m.%Y'), 'D')
index = pd.date_range(first_date_str, periods=DAYS)
columns = pd.date_range('1900-01-01 00:00', freq="5min", periods=STEPS)
data = pd.DataFrame(NV, columns=columns, index=index)

# przepisanie wczytanych danych do macierzy
for i in range(len(read_data)):
    row = np.datetime64(datetime.datetime.strptime(read_data.iloc[i]['date'], '%d.%m.%Y'), 'D')
    column = round_time(datetime.datetime.strptime(read_data.iloc[i]['time'], '%H:%M:%S'))
    value = read_data.iloc[i]['temp']
    data.at[row, column] = value

# eksport macierzy
data.to_csv('dane\\macierz.csv', sep=';', decimal=',')

# wyeliminowanie pustych danych (przeprowadzenie lini prostej od ostatniej odczytanej wartosci do kolejnej)
begin_value = end_value = data.iat[0, 0]
i = 1
while i < LEN:
    if data.iat[item_to_coordinate(i, ROWS)] == NV:
        j = i
        while j < LEN:
            end_value = data.iat[item_to_coordinate(j, ROWS)]
            if end_value != NV:
                break
            j += 1
        delta = (end_value - begin_value)/(j - i + 1)
        k = i
        while k <= j:
            data.iat[item_to_coordinate(k, ROWS)] = begin_value + (k - i + 1)*delta
            k += 1
    begin_value = data.iat[item_to_coordinate(i, ROWS)]
    i += 1

# wykreslenie danych
X = np.arange(1, DAYS+1, 1).reshape(DAYS, 1)
Y = np.arange(1, STEPS+1, 1).reshape(1, STEPS)
Z = data.values

ax = plt.axes(projection='3d')
ax.set_ylabel('h')
ax.set_zlabel('C')
ax.set_yticklabels(['0', '6', '12', '18', '24'])
ax.set_yticks((0, 72, 144, 216, 288))
ax.set_xticklabels([read_data.iloc[0]['date'], read_data.iloc[-1]['date']])
ax.set_xticks((1, DAYS))
ax.plot_surface(X, Y, Z, cmap=plt.cm.jet, rstride=1, cstride=1, linewidth=0)
ax.view_init(elev=60, azim=150)
ax.invert_yaxis()

plt.show()
