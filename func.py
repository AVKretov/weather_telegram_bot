def wind_deg_to_str(deg):
    if deg >= 11.25 and deg < 33.75:
        return 'Северо-северо-восток'
    elif deg >= 33.75 and deg < 56.25:
        return 'Северо-восток'
    elif deg >= 56.25 and deg < 78.75:
        return 'Востоко-северо-восток'
    elif deg >= 78.75 and deg < 101.25:
        return 'Восток'
    elif deg >= 101.25 and deg < 123.75:
        return 'Востоко-юго-восток'
    elif deg >= 123.75 and deg < 146.25:
        return 'Юго-восток'
    elif deg >= 146.25 and deg < 168.75:
        return 'Юго-юго-восток'
    elif deg >= 168.75 and deg < 191.25:
        return 'Юг'
    elif deg >= 191.25 and deg < 213.75:
        return 'Юго-юго-запад'
    elif deg >= 213.75 and deg < 236.25:
        return 'Юго-запад'
    elif deg >= 236.25 and deg < 258.75:
        return 'Западо-юго-запад'
    elif deg >= 258.75 and deg < 281.25:
        return 'Запад'
    elif deg >= 281.25 and deg < 303.75:
        return 'Западо-северо-запад'
    elif deg >= 303.75 and deg < 326.25:
        return 'Северо-запад'
    elif deg >= 326.25 and deg < 348.75:
        return 'Северо-северо-запад'
    else:
        return 'Север'

def fibonacci(n):

    a, b = 0, 1
    c =0
    res = []
    while c <= n:
        if a+b %2 ==0:
            res.append(a+b)
            c += 1
    a, b = b, a + b
    return res

