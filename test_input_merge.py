import pandas as pd

WEATHER_DATA_PATH = "10Dec-22Nov.txt"
SETPOINT_DATA_PATH = "SP_10Dec-22Nov.txt"
SCREEN_USABLE_PATH = "SC_usable_10Dec-22Nov.txt"

# 파일 읽기 (헤더 포함, skiprows 없이)
weather = pd.read_csv(WEATHER_DATA_PATH, sep='\t')
setpoint = pd.read_csv(SETPOINT_DATA_PATH, sep='\t')
sc_usable = pd.read_csv(SCREEN_USABLE_PATH, sep='\t')

# 컬럼명 앞뒤 공백 제거
weather.columns = weather.columns.str.strip()
setpoint.columns = setpoint.columns.str.strip()
sc_usable.columns = sc_usable.columns.str.strip()

# 컬럼명 통일 (필요시)
weather = weather.rename(columns={weather.columns[0]: 'time'})
setpoint = setpoint.rename(columns={setpoint.columns[0]: 'time'})
sc_usable = sc_usable.rename(columns={sc_usable.columns[0]: 'time'})

# time 기준 merge (outer join)
df = pd.merge(weather, setpoint, on='time', how='outer')
df = pd.merge(df, sc_usable, on='time', how='outer')
# 시간순 정렬
df = df.sort_values('time').reset_index(drop=True)
# 결측치 선형 보간
df = df.interpolate(method='linear', limit_direction='both')

# 컬럼명 및 데이터프레임 출력
print("컬럼명:", df.columns.tolist())
print(df) 