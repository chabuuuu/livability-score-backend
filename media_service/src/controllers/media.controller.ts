import { MediaService } from "@/services/media.service";
import BaseError from "@/utils/base.error";
import { GlobalConfig } from "@/utils/config/global-config.util";
import { Request, Response, NextFunction } from "express";
import { v4 as uuidv4 } from "uuid";

export class MediaController {
  private mediaService: MediaService;

  constructor() {
    this.mediaService = new MediaService(); // Khởi tạo service
  }

  async uploadImage(req: Request, res: Response, next: NextFunction) {
    if (!req.file) {
      return res.send_badRequest("No file uploaded or file is too large.");
    }

    try {
      const tempFilePath = req.file.path;

      const result = await this.mediaService.uploadImage(tempFilePath);
      res.send_ok("Upload image successfully", result);
    } catch (error) {
      throw new BaseError("UNKNOWN", "Upload image failed");
    }
  }

  async uploadVideo(req: Request, res: Response, next: NextFunction) {
    if (!req.file) {
      return res.send_badRequest("No file uploaded or file is too large.");
    }

    try {
      const tempFilePath = req.file.path;
      const fileName = uuidv4();

      const bucketName = GlobalConfig.media_service.video_bucket.path;

      const result = {
        mediaUrl:
          GlobalConfig.media_service.url + "/" + bucketName + "/" + fileName,
      };

      this.mediaService.uploadVideo(fileName, tempFilePath);

      res.send_ok("Upload video successfully", result);
    } catch (error) {
      throw new BaseError("UNKNOWN", "Upload video failed");
    }
  }

  async getVideoUrl(req: Request, res: Response, next: NextFunction) {
    try {
      const result = await this.mediaService.getVideoUrl();
      res.send_ok("Get video url successfully", result);
    } catch (error) {
      throw new BaseError("UNKNOWN", "Get video url failed");
    }
  }
}
