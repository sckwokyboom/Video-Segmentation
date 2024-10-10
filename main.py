import cv2
import numpy as np
from moviepy.editor import VideoFileClip
import moviepy.editor as mp
from pathlib import Path
from loguru import logger
import concurrent.futures
import os

logger.add("video_processing.log", format="{time} {level} {message}", level="INFO")


def check_video_format(video_path):
    """Проверяет, поддерживается ли формат видео, и конвертирует при необходимости."""
    supported_formats = ['.mp4', '.avi', '.mov']
    video_ext = Path(video_path).suffix.lower()

    if video_ext not in supported_formats:
        logger.error(f"Неподдерживаемый формат видео: {video_ext}. Конвертация требуется.")
        raise ValueError(f"Формат {video_ext} не поддерживается. Конвертируйте видео в MP4 или AVI.")

    logger.info(f"Формат видео поддерживается: {video_ext}")


def get_frame_diff(frame1, frame2):
    return cv2.absdiff(frame1, frame2)


def is_similar(frame1, frame2, threshold=30):
    diff = get_frame_diff(frame1, frame2)
    return np.mean(diff) < threshold


def process_frame_segment(video_path, temp_video_path, start_frame, end_frame, threshold=30):
    """Обработка сегмента видео для замены похожих кадров."""
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    out = cv2.VideoWriter(temp_video_path, fourcc, fps, (width, height))
    ret, prev_frame = cap.read()

    original_frame_count = 0
    unique_frame_count = 0

    for i in range(start_frame, end_frame):
        ret, frame = cap.read()
        if not ret:
            break
        original_frame_count += 1
        if not is_similar(prev_frame, frame, threshold):
            out.write(frame)
            prev_frame = frame
            unique_frame_count += 1
        else:
            out.write(prev_frame)

    cap.release()
    out.release()

    return original_frame_count, unique_frame_count


def replace_similar_frames(video_path, temp_video_path, threshold=30, workers=4):
    """Замена похожих кадров на репрезентативные с использованием многопоточности."""
    check_video_format(video_path)
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)  # Получаем частоту кадров
    cap.release()

    if fps == 0:
        logger.error("Не удалось получить частоту кадров (FPS) для видео.")
        raise ValueError("FPS не определён. Проверьте видеофайл.")


    logger.info(f"Используемый порог для сравнения кадров (threshold): {threshold}")

    segment_size = frame_count // workers
    futures = []

    total_original_frames = 0
    total_final_frames = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for i in range(workers):
            start_frame = i * segment_size
            end_frame = (i + 1) * segment_size if i < workers - 1 else frame_count
            segment_temp_video_path = f"{temp_video_path}_{i}.mp4"
            futures.append(
                executor.submit(process_frame_segment, video_path, segment_temp_video_path, start_frame, end_frame,
                                threshold))

    concurrent.futures.wait(futures)

    for future in concurrent.futures.as_completed(futures):
        original_frame_count, final_frame_count = future.result()
        total_original_frames += original_frame_count
        total_final_frames += final_frame_count

    logger.info(f"Изначальное количество кадров: {frame_count}")
    logger.info(f"Количество кадров после обработки: {total_final_frames}")

    # Объединение сегментов
    merge_video_segments(temp_video_path, workers)


def merge_video_segments(temp_video_base_path, workers):
    """Объединение обработанных сегментов видео в один файл."""
    clips = []
    for i in range(workers):
        segment_path = f"{temp_video_base_path}_{i}.mp4"
        clip = mp.VideoFileClip(segment_path)
        clips.append(clip)

    logger.info("Объединение всех видеофрагментов в один клип")
    final_clip = mp.concatenate_videoclips(clips, method="compose")

    output_temp_path = f"{temp_video_base_path}_merged.mp4"
    final_clip.write_videofile(output_temp_path, codec="libx264")

    return output_temp_path


def merge_audio_video(original_video_path, temp_video_path, output_video_path):
    """Слияние изменённого видео с аудио из оригинального файла."""
    original_clip = VideoFileClip(original_video_path)

    # Проверка наличия аудио в оригинальном видео
    if original_clip.audio is None:
        logger.error("В оригинальном видео отсутствует аудиопоток.")
        raise ValueError("Оригинальное видео не содержит аудио.")

    if not os.path.exists(f"{temp_video_path}.mp4"):
        logger.error(f"Временный файл видео не найден: {temp_video_path}.mp4")
        raise FileNotFoundError(f"Файл {temp_video_path}.mp4 не найден.")

    new_clip = VideoFileClip(f"{temp_video_path}.mp4")
    logger.error("Загружено temp_video.mp4 для обработки}")

    logger.info("Слияние аудио с видео")
    final_clip = new_clip.set_audio(original_clip.audio)
    final_clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")


def process_video(input_video, output_video, threshold=30, workers=4):
    """Главная функция для обработки видео."""
    try:
        logger.info(f"Начало обработки видео: {input_video}")
        temp_video = 'temp_video'
        replace_similar_frames(input_video, temp_video, threshold, workers)
        logger.info("Заменённые кадры успешно сохранены во временное видео")
        merge_audio_video(input_video, temp_video + "_merged", output_video)
        logger.info(f"Видео успешно обработано и сохранено как {output_video}")
    except Exception as e:
        logger.error(f"Ошибка при обработке видео: {e}")


# Пример использования
input_video_path = 'garry_potter.mp4'
output_video_path = 'new_output_garry_potter_scene.mp4'

process_video(input_video_path, output_video_path, threshold=17, workers=4)
