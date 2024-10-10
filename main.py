import cv2
import numpy as np


def get_frame_diff(frame1, frame2):
    return cv2.absdiff(frame1, frame2)


def is_similar(frame1, frame2, threshold=30):
    diff = get_frame_diff(frame1, frame2)
    return np.mean(diff) < threshold


def replace_similar_frames_with_audio(video_path, output_video_path, threshold=30):
    # Чтение исходного видео
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Ошибка открытия видеофайла")
        return

    # Получаем параметры видео
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    # Открываем видео для записи
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

    # Получаем первый кадр
    ret, prev_frame = cap.read()
    if not ret:
        print("Не удалось получить кадры")
        return

    out.write(prev_frame)  # Записываем первый кадр как есть

    # Обрабатываем последующие кадры
    for i in range(1, frame_count):
        ret, frame = cap.read()
        if not ret:
            break

        # Сравниваем текущий кадр с предыдущим
        if not is_similar(prev_frame, frame, threshold):
            out.write(frame)  # Записываем кадр только если он отличается
            prev_frame = frame  # Обновляем предыдущий кадр

        else:
            out.write(prev_frame)  # Записываем репрезентативный кадр

    # Освобождаем видеофайлы
    cap.release()
    out.release()

    print(f"Обработка завершена, видео сохранено как {output_video_path}")


# Пример использования
replace_similar_frames_with_audio('video.mp4', 'output_video.mp4')
