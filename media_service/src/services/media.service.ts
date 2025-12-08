import { GetMediaUrlRes } from "@/dto/get-image-url.res";
import { MediaUploadRes } from "@/dto/media-upload.res";
import { GlobalConfig } from "@/utils/config/global-config.util";
import minioClient from "@/utils/minio-instance.util";
import fs from "fs";
import { v4 as uuidv4 } from "uuid";

export class MediaService {
  async uploadImage(tempFilePath: string): Promise<MediaUploadRes> {
    const bucketName = GlobalConfig.media_service.image_bucket.path;

    // Generate a unique file name
    const fileName = uuidv4();

    await minioClient.fPutObject(bucketName, fileName, tempFilePath);

    // Xóa file tạm sau khi upload
    fs.unlink(tempFilePath, (unlinkErr) => {
      if (unlinkErr) {
        console.error("Error deleting temp file:", unlinkErr);
      }
    });

    return {
      mediaUrl:
        GlobalConfig.media_service.url + "/" + bucketName + "/" + fileName,
    };
  }

  async getVideoUrl(): Promise<GetMediaUrlRes> {
    const bucketName = GlobalConfig.media_service.video_bucket.path;
    const fileName = uuidv4();
    return {
      mediaUrl:
        GlobalConfig.media_service.url + "/" + bucketName + "/" + fileName,
      fileName: fileName,
    };
  }

  async uploadVideo(
    fileName: string,
    tempFilePath: string
  ): Promise<MediaUploadRes> {
    const bucketName = GlobalConfig.media_service.video_bucket.path;
    await minioClient.fPutObject(bucketName, fileName, tempFilePath);

    // Xóa file tạm sau khi upload
    fs.unlink(tempFilePath, (unlinkErr) => {
      if (unlinkErr) {
        console.error("Error deleting temp file:", unlinkErr);
      }
    });

    return {
      mediaUrl:
        GlobalConfig.media_service.url + "/" + bucketName + "/" + fileName,
    };
  }
}
