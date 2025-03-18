import torch
import rembg
import cv2
import numpy as np

from diffusers import AutoencoderKL, ControlNetModel, StableDiffusionXLControlNetPipeline
from diffusers.models import UNet2DConditionModel
from diffusers.schedulers import DPMSolverMultistepScheduler
from diffusers.utils import load_image

from transformers import CLIPTokenizer, CLIPTextModel

from insightface.app import FaceAnalysis


class InstantIDPipeline:
	def __init__(self, device="cuda"):
		self.device = device

		print("Loading base sd model...")
		self.base_model_path = "stabilityai/stable-diffusion-xl-base-1.0"

		self.vae = AutoencoderKL.from_pretrained(
			self.base_model_path,
			subfolder='vae',
			# torch_type=torch.float16
		).to(self.device)

		self.unet = UNet2DConditionModel.from_pretrained(
			self.base_model_path,
			subfolder='unet',
			# torch_type=torch.float16
		).to(self.device)

		self.tokenizer = CLIPTokenizer.from_pretrained(
			self.base_model_path,
			subfolder='tokenizer',
			# torch_type=torch.float16
		)
		self.tokenizer_2 = CLIPTokenizer.from_pretrained(
			self.base_model_path,
			subfolder='tokenizer_2',
			# torch_type=torch.float16
		)
		self.text_encoder = CLIPTextModel.from_pretrained(
			self.base_model_path,
			subfolder='text_encoder',
			# torch_type=torch.float16
		).to(self.device)
		self.text_encoder_2 = CLIPTextModel.from_pretrained(
			self.base_model_path,
			subfolder='text_encoder_2',
			# torch_type=torch.float16
		).to(self.device)

		print("Loading InstantID models...")
		controlnet_path = "./models/controlnet/instantid/diffusion_pytorch_model.safetensors"
		self.controlnet = ControlNetModel.from_single_file(
			controlnet_path,
			# torch_type=torch.float16
		).to(self.device)

		fa_root_path = "./models/insightface"
		self.face_analyzer = FaceAnalysis(
			name='antelopev2',
			root=fa_root_path,
			providers=['CPUExecutionProvider']
		)
		self.face_analyzer.prepare(ctx_id=0, det_size=(640, 640))

		ip_adapter_path = "./models/instantid/ip-adapter.bin"
		self.ip_model = torch.load(
			ip_adapter_path,
			map_location=self.device
		)

		self.scheduler = DPMSolverMultistepScheduler.from_pretrained(
			self.base_model_path,
			subfolder='scheduler'
		)

		print("Loading SD models...")
		checkpoint_path = "./models/sd/dreamshaperXL_lightningDPMSDE.safetensors"
		self.pipeline = StableDiffusionXLControlNetPipeline.from_single_file(
			checkpoint_path,
			vae=self.vae,
			text_encoder=self.text_encoder,
			text_encoder_2=self.text_encoder_2,
			tokenizer=self.tokenizer,
			tokenizer_2=self.tokenizer_2,
			unet=self.unet,
			controlnet=self.controlnet,
			scheduler=self.scheduler,
			requires_safety_checker=False,
			safety_checker=None,
			feature_extractor=None,
		).to(self.device)

		lora_path = "./models/lora/Stickers Redmond.safetensors"
		self.pipeline.load_lora_weights(lora_path)

		self.rembg_session = rembg.new_session()

		print("All models loaded successfully!")

	def generate(self, face_image_path, prompt, negative_prompt=None):
		if negative_prompt is None:
			negative_prompt = "shiny, photo, photography, soft, nsfw, nude, ugly, broken, watermark, oversaturated"

		face_image = load_image(face_image_path)

		face_emb, face_kps = self._get_face_embeds(face_image)

		# first_stage_image = self._apply_instantid(
        #     face_emb,
        #     face_kps,
        #     prompt=prompt,
        #     negative_prompt=negative_prompt,
        #     controlnet_conditioning_scale=1.0,  # AutomaticCFG에서 설정된 값
        #     ip_adapter_scale=1.0,               # ApplyInstantID의 첫번째 값
        # )

		# final_image = self._apply_instantid(
        #     face_emb,
        #     face_kps,
        #     prompt=prompt + ", Sticker, svg, vector art, sharp, kawaii style, Anime style",  # Text Concatenate 추가 부분
        #     negative_prompt=negative_prompt,
        #     controlnet_conditioning_scale=0.0,  # 두 번째 단계에서는 ControlNet 제거
        #     ip_adapter_scale=1.0,
        # )

		# final_image_no_bg = self._remove_background(final_image)
		image = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=face_kps,  # ControlNet 입력
            # controlnet_conditioning_scale=controlnet_conditioning_scale,
            num_inference_steps=8,   # 워크플로우에서 KSampler가 8 steps 사용
            guidance_scale=4.0,      # 워크플로우에서 KSampler가 4.0 CFG 사용
            generator=torch.manual_seed(378971921426134),  # 워크플로우에서 사용된 시드값
            width=1024,
            height=1024,
        ).images[0]

		return {
			"image": image,
        #     "face_image": face_image,
        #     "first_stage": first_stage_image,
        #     "final_image": final_image,
        #     "final_image_no_bg": final_image_no_bg
        }

	def _remove_background(self, image):
		return rembg.remove(image, session=self.rembg_session)

	def _apply_instantid(self, face_emb, face_kps, prompt, negative_prompt, controlnet_conditioning_scale=1.0, ip_adapter_scale=0.8):
        # IP-Adapter 임베딩 준비
		cond_embeds = self._get_ip_adapter_embeds(face_emb)

        # ControlNet 입력용 얼굴 랜드마크 이미지 준비
		face_kps_np = np.zeros((256, 256, 3))
		for i in range(face_kps.shape[0]):
			x, y = face_kps[i]
			x, y = int(x), int(y)
			cv2.circle(face_kps_np, (x, y), 3, (255, 255, 255), -1)

		face_kps_tensor = torch.from_numpy(face_kps_np).float() / 255.0
		face_kps_tensor = face_kps_tensor.permute(2, 0, 1).unsqueeze(0).to(self.device, dtype=torch.float16)

        # IP-Adapter를 UNet에 적용
		attn_processors = self.pipeline.unet.attn_processors.copy()

		# 어텐션 레이어의 정확한 이름과 개수 파악
		attention_module_count = 0
		attention_module_names = []
		for name, _ in self.pipeline.unet.attn_processors.items():
			attention_module_names.append(name)
			attention_module_count += 1
		print(f"모델에는 {attention_module_count}개의 어텐션 레이어가 있습니다.")
		print(f"첫 5개 레이어 이름: {attention_module_names[:5]}")

		# 정확한 이름 패턴으로 attn2 레이어만 업데이트
		updated_count = 0
		for name in attention_module_names:
			if name.endswith("attn2"):
				# 해당 모듈 찾기
				module = self.pipeline.unet
				for part in name.split('.'):
					if hasattr(module, part):
						module = getattr(module, part)
					else:
						print(f"모듈 {name}을 찾을 수 없습니다.")
						break

				# 찾은 모듈이 적합한지 확인
				if hasattr(module, "to_k"):
					cross_attention_dim = module.to_k.in_features
					attn_processors[name] = IPAdapterAttnProcessor(
						hidden_size=cross_attention_dim,
						ip_adapter_scale=ip_adapter_scale,
						ip_adapter_embeds=cond_embeds,
					)
					updated_count += 1

		print(f"{updated_count}개의 attn2 레이어를 업데이트했습니다.")
		self.pipeline.unet.set_attn_processor(attn_processors)

		image = self.pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=face_kps_tensor,  # ControlNet 입력
            controlnet_conditioning_scale=controlnet_conditioning_scale,
            num_inference_steps=8,   # 워크플로우에서 KSampler가 8 steps 사용
            guidance_scale=4.0,      # 워크플로우에서 KSampler가 4.0 CFG 사용
            generator=torch.manual_seed(378971921426134),  # 워크플로우에서 사용된 시드값
            width=1024,
            height=1024,
        ).images[0]

		return image

	def _get_face_embeds(self, face_image):
		if not isinstance(face_image, np.ndarray):
			face_image = np.array(face_image)

		face_image = cv2.cvtColor(face_image, cv2.COLOR_RGB2BGR)
		faces = self.face_analyzer.get(face_image)

		if len(faces) == 0:
			raise Exception("No faces detected in the image!")

		face_info = faces[0]

		return face_info.embedding, face_info.kps

	def _get_ip_adapter_embeds(self, face_emb):
		ip_layers = self.ip_model["ip_adapter"]

		# NumPy 배열을 PyTorch 텐서로 변환
		if isinstance(face_emb, np.ndarray):
			face_emb = torch.from_numpy(face_emb)

		# Mac M4에서는 float32 사용 (또는 디바이스에 맞는 dtype 사용)
		device_dtype = torch.float32 if self.device == "mps" else torch.float16

		# reshape 후 디바이스로 이동
		pixel_embeds = face_emb.reshape(1, 1, -1).to(self.device, dtype=device_dtype)

		pixel_values = None
		ip_hidden_states = None

		cond_embeds = []
		for i, ip_layer in enumerate(ip_layers):
			if ip_layer is not None and callable(ip_layer):
				cond_embed = ip_layer(
					pixel_embeds,
					pixel_values,
					image_embeds=ip_hidden_states
				)
				cond_embeds.append(cond_embed)
			else:
				cond_embeds.append(None)

		return cond_embeds


class IPAdapterAttnProcessor:
    def __init__(self, hidden_size, ip_adapter_scale=1.0, ip_adapter_embeds=None):
        self.hidden_size = hidden_size
        self.ip_adapter_scale = ip_adapter_scale
        self.ip_adapter_embeds = ip_adapter_embeds

    def __call__(self, attn, hidden_states, encoder_hidden_states=None, attention_mask=None):
        batch_size, sequence_length, _ = hidden_states.shape
        attention_mask = attn.prepare_attention_mask(attention_mask, sequence_length, batch_size)
        query = attn.to_q(hidden_states)

        is_cross_attention = encoder_hidden_states is not None
        if is_cross_attention:
            key = attn.to_k(encoder_hidden_states)
            value = attn.to_v(encoder_hidden_states)

            # IP-Adapter 임베딩 처리
            if self.ip_adapter_embeds is not None:
                # 배치 차원 확인 및 조정
                if isinstance(self.ip_adapter_embeds, list):
                    # 리스트 형태의 임베딩 처리
                    for ip_embed in self.ip_adapter_embeds:
                        if ip_embed is not None:
                            # ip_embed가 텐서 형태이면 직접 사용
                            if hasattr(ip_embed, 'k') and hasattr(ip_embed, 'v'):
                                key_ip = ip_embed.k
                                value_ip = ip_embed.v
                            else:  # 텐서 자체가 전달된 경우
                                # 배치 차원 맞추기
                                if ip_embed.shape[0] != batch_size:
                                    ip_embed = ip_embed.repeat(batch_size, 1, 1)
                                # key, value 투영
                                key_ip = attn.to_k(ip_embed)
                                value_ip = attn.to_v(ip_embed)

                            key = torch.cat([key, key_ip], dim=1)
                            value = torch.cat([value, value_ip], dim=1)
                else:
                    # 단일 텐서 형태의 임베딩 처리
                    ip_embed = self.ip_adapter_embeds
                    # 배치 차원 맞추기
                    if len(ip_embed.shape) == 2:  # [seq_len, hidden_dim]
                        ip_embed = ip_embed.unsqueeze(0).repeat(batch_size, 1, 1)
                    elif ip_embed.shape[0] != batch_size:
                        ip_embed = ip_embed.repeat(batch_size, 1, 1)

                    # key, value 투영
                    key_ip = attn.to_k(ip_embed)
                    value_ip = attn.to_v(ip_embed)

                    # 스케일 적용
                    key_ip = key_ip * self.ip_adapter_scale
                    value_ip = value_ip * self.ip_adapter_scale

                    key = torch.cat([key, key_ip], dim=1)
                    value = torch.cat([value, value_ip], dim=1)
        else:
            key = attn.to_k(hidden_states)
            value = attn.to_v(hidden_states)

        query = attn.head_to_batch_dim(query)
        key = attn.head_to_batch_dim(key)
        value = attn.head_to_batch_dim(value)

        attention_probs = attn.get_attention_scores(query, key, attention_mask)
        hidden_states = torch.bmm(attention_probs, value)
        hidden_states = attn.batch_to_head_dim(hidden_states)

        # linear proj
        hidden_states = attn.to_out[0](hidden_states)
        # dropout
        hidden_states = attn.to_out[1](hidden_states)

        return hidden_states

if __name__ == "__main__":
	pipeline = InstantIDPipeline(device="mps")

	face_image_path = "./samples/image.jpg"
	prompt = "half body, looking at viewer, 1 boy, running"
	negative_prompt = "shiny, photo, photography, soft, nsfw, nude, ugly, broken, watermark, oversaturated"

	results = pipeline.generate(face_image_path, prompt, negative_prompt)

	print("Pipeline loaded successfully!")