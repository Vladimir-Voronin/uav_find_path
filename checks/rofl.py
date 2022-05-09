import os


# Определить функцию
def get_lines_by_suffix(path, suffix):
    # Установить code_lines как глобальную переменную
    global code_lines
    # Список файлов и папок по пути, исключая вложенные файлы и подпапки
    file_list = os.listdir(path)
    # Просматривать перечисленные файлы и папки, если это папка, искать рекурсивно, если это файл, подсчитывать количество строк кода
    for filename in file_list:
        # путь и имя файла вместе образуют полный путь к запрашиваемому файлу или папке
        file_path = os.path.join(path, filename)
        # Если это папка
        if os.path.isdir(file_path):
            # Рекурсивный поиск
            get_lines_by_suffix(file_path, suffix)
        else:
            if file_path.split(".")[-1] == suffix:
                # Подсчитываем количество строк кода
                code_lines += get_lines(file_path)
                # Просмотр для печати
                print(code_lines)
        # После завершения рекурсивного поиска вернуть количество всех кодов
    return code_lines


# Определить функцию, функцию, используемую для вычисления кода в одном файле
def get_lines(file):
    # Открыть (подключить) файл
    with open(file, encoding="utf-8") as f:
        # Получаем количество прочитанных строк, то есть количество строк кода в файле
        return len(f.readlines())


# Тестовая проверка
a = get_lines_by_suffix(
    r"C:\Users\Neptune\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\uav_find_path",
    "py")
print(a)
