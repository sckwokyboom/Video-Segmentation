import cv2
import numpy as np
from moviepy.editor import VideoFileClip


def get_frame_diff(frame1, frame2):
    return cv2.absdiff(frame1, frame2)


def is_similar(frame1, frame2, threshold=30):
    diff = get_frame_diff(frame1, frame2)
    return np.mean(diff) < threshold


def replace_similar_frames(video_path, temp_video_path, threshold=30):
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
    out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))

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


def merge_audio_video(original_video_path, temp_video_path, output_video_path):
    # Извлечение аудио и объединение с видео
    original_clip = VideoFileClip(original_video_path)
    new_clip = VideoFileClip(temp_video_path)

    # Слияние аудио из оригинального видео с новым видео
    final_clip = new_clip.set_audio(original_clip.audio)
    final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")


# Пример использования
input_video = 'video.mp4'
temp_video = 'temp_video.mp4'
output_video = 'output_video_with_audio.mp4'

replace_similar_frames(input_video, temp_video)
merge_audio_video(input_video, temp_video, output_video)
