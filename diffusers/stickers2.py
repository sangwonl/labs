import os
import torch
import numpy as np
import PIL
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline, StableDiffusionInpaintPipeline, StableDiffusionControlNetPipeline
from diffusers.utils import load_image
from diffusers import ControlNetModel, UniPCMultistepScheduler
from controlnet_aux import OpenposeDetector, MLSDdetector
import cv2
from typing import List, Tuple, Dict, Optional

class PersonalizedStickerGenerator:
    def __init__(self, device="cuda" if torch.cuda.is_available() else "mps"):
        self.device = device
        print(f"Using device: {self.device}")

        # ControlNet 모델 로드 (OpenPose 버전) - 사람의 자세를 제어하기 위함
        self.controlnet = ControlNetModel.from_pretrained(
            "lllyasviel/sd-controlnet-openpose",
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)

        # 1. 기본 이미지 변환 파이프라인
        self.img2img_pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)

        # 2. ControlNet 기반 파이프라인 (자세 제어용)
        self.controlnet_pipeline = StableDiffusionControlNetPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            controlnet=self.controlnet,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
        ).to(self.device)

        # 더 빠른 스케줄러 사용
        self.controlnet_pipeline.scheduler = UniPCMultistepScheduler.from_config(
            self.controlnet_pipeline.scheduler.config
        )

        # OpenPose 감지기 로드
        self.openpose_detector = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")

        print("모든 모델 로딩 완료!")

    def preprocess_image(self, image_path: str, target_size: Tuple[int, int] = (512, 512)) -> PIL.Image.Image:
        """입력 이미지를 전처리합니다."""
        image = load_image(image_path)

        # 이미지 리사이징 (비율 유지)
        width, height = image.size
        ratio = min(target_size[0] / width, target_size[1] / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        image = image.resize((new_width, new_height), PIL.Image.LANCZOS)

        # 패딩 적용해서 정사각형으로 만들기
        new_image = PIL.Image.new("RGB", target_size, (255, 255, 255))
        paste_x = (target_size[0] - new_width) // 2
        paste_y = (target_size[1] - new_height) // 2
        new_image.paste(image, (paste_x, paste_y))

        return new_image

    def extract_pose(self, image: PIL.Image.Image) -> PIL.Image.Image:
        """OpenPose를 사용하여 이미지에서 자세 추출"""
        pose_image = self.openpose_detector(image)
        return pose_image

    def generate_sticker_openpose_control(
        self,
        image_path: str,
        pose: str,
        style: str = "cartoon sticker, cute, simple background",
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        strength: float = 0.75
    ) -> PIL.Image.Image:
        """
        ControlNet을 사용하여 이미지의 인물을 특정 자세를 취하는 스티커로 변환합니다.

        Args:
            image_path: 원본 인물 이미지 경로
            pose: 원하는 자세 설명 (예: "running", "reading a book")
            style: 스티커 스타일
            num_inference_steps: 추론 단계 수
            guidance_scale: 가이던스 스케일
            strength: 원본 이미지 영향력 (낮을수록 원본과 더 유사)

        Returns:
            생성된 스티커 이미지
        """
        # 이미지 전처리
        input_image = self.preprocess_image(image_path)

        # 원본 이미지에서 포즈 추출 (참조용)
        original_pose = self.extract_pose(input_image)

        # 프롬프트 구성
        prompt = f"a {pose} person, {style}, chibi, emoticon style, white background, simplified, flat colors"
        negative_prompt = "blurry, low quality, distorted, deformed, ugly, unrealistic proportions"

        # 이미지 생성
        result = self.img2img_pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=input_image,
            strength=strength,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
        ).images[0]

        return result

    def generate_sticker_with_pose_control(
        self,
        image_path: str,
        pose: str,
        style: str = "cartoon sticker, cute, simple background",
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
    ) -> PIL.Image.Image:
        """
        ControlNet OpenPose를 사용해 특정 자세를 가진 스티커를 생성합니다.
        이 방법은 자세를 더 명확하게 통제할 수 있습니다.

        Args:
            image_path: 원본 인물 이미지 경로
            pose: 원하는 자세 설명 (예: "running", "reading a book")
            style: 스티커 스타일
            num_inference_steps: 추론 단계 수
            guidance_scale: 가이던스 스케일

        Returns:
            생성된 스티커 이미지
        """
        # 이미지 전처리
        input_image = self.preprocess_image(image_path)

        # 특정 자세와 관련된 텍스트 프롬프트로 포즈 이미지 생성
        # 포즈 이미지 생성을 위한 초기 이미지
        initial_prompt = f"a person {pose}, full body, clear pose"
        negative_prompt = "blurry, low quality, cropped, unrealistic proportions"

        # 초기 이미지 생성 (자세를 가진)
        initial_result = self.img2img_pipeline(
            prompt=initial_prompt,
            negative_prompt=negative_prompt,
            image=input_image,
            strength=0.8,  # 원본 인물의 특징을 일부 유지하면서 자세 변형
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
        ).images[0]

        # 생성된 초기 이미지에서 포즈 추출
        pose_image = self.extract_pose(initial_result)

        # ControlNet을 사용하여 최종 스티커 생성
        prompt = f"a {pose} person, {style}, chibi, emoticon style, white background, simplified, flat colors"
        negative_prompt = "blurry, low quality, distorted, deformed, ugly, unrealistic proportions"

        result = self.controlnet_pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=pose_image,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
        ).images[0]

        return result

    def create_sticker_set(
        self,
        image_path: str,
        poses: List[str],
        output_dir: str = "stickers",
        style: str = "cartoon sticker, cute, simple background",
    ) -> List[str]:
        """
        여러 자세의 스티커 세트를 생성합니다.

        Args:
            image_path: 원본 인물 이미지 경로
            poses: 생성할 자세 목록 (예: ["running", "jumping", "reading"])
            output_dir: 스티커를 저장할 디렉토리
            style: 스티커 스타일

        Returns:
            생성된 스티커 이미지 경로 목록
        """
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)

        output_paths = []

        # 각 자세별로 스티커 생성
        for pose in poses:
            print(f"자세 '{pose}' 스티커 생성 중...")

            # 두 가지 방식으로 생성해보고 더 나은 것 선택
            sticker1 = self.generate_sticker_openpose_control(
                image_path=image_path,
                pose=pose,
                style=style
            )

            sticker2 = self.generate_sticker_with_pose_control(
                image_path=image_path,
                pose=pose,
                style=style
            )

            # 저장
            filename1 = os.path.join(output_dir, f"{pose}_sticker1.png")
            filename2 = os.path.join(output_dir, f"{pose}_sticker2.png")

            sticker1.save(filename1)
            sticker2.save(filename2)

            output_paths.extend([filename1, filename2])
            print(f"'{pose}' 스티커 저장 완료: {filename1}, {filename2}")

        return output_paths

    def enhance_sticker_background(
        self,
        sticker_path: str,
        output_path: str = None,
        background_color: Tuple[int, int, int] = (255, 255, 255, 0)  # 투명 배경
    ) -> PIL.Image.Image:
        """
        스티커 배경을 개선하여 투명하게 만듭니다.

        Args:
            sticker_path: 스티커 이미지 경로
            output_path: 출력 이미지 경로 (None이면 저장하지 않음)
            background_color: 배경색 (기본값: 투명)

        Returns:
            개선된 스티커 이미지
        """
        # 이미지 로드
        image = Image.open(sticker_path).convert("RGBA")

        # 이미지를 numpy 배열로 변환
        data = np.array(image)

        # 배경색에 가까운 픽셀을 투명하게 설정 (간단한 방법)
        # 흰색 배경 가정 (더 정교한 방법은 배경 제거 알고리즘 사용 필요)
        r, g, b, a = data[:,:,0], data[:,:,1], data[:,:,2], data[:,:,3]
        mask = (r > 240) & (g > 240) & (b > 240)
        data[:,:,3] = np.where(mask, 0, 255)

        # 다시 PIL 이미지로 변환
        result = Image.fromarray(data)

        # 저장
        if output_path:
            result.save(output_path, format="PNG")

        return result

# 사용 예시
if __name__ == "__main__":
	os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

	generator = PersonalizedStickerGenerator()

    # 인물 사진 경로
	person_image = "./samples/image.jpg"  # 인물 사진 경로로 변경하세요

    # 원하는 자세 목록
	poses = ["running", "reading a book", "jumping", "waving hello", "thumbs up", "thinking", "dancing"]

    # 스티커 생성
	output_paths = generator.create_sticker_set(
        image_path=person_image,
        poses=poses,
        style="cartoon sticker, cute, simple, flat illustration, vector art style"
    )

    # 배경 개선 (투명화)
	for path in output_paths:
		transparent_path = path.replace(".png", "_transparent.png")
		generator.enhance_sticker_background(path, transparent_path)
		print(f"투명 배경 스티커 저장: {transparent_path}")

	print("모든 스티커 생성 완료!")
