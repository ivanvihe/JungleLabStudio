
import { VideoResource } from '../types/video';

const localVideos: VideoResource[] = [
  {
    id: 'Nature_Fox',
    title: 'Nature Fox',
    description: 'A fox in its natural habitat.',
    thumbnail: '/videos/Nature_Fox.jpg', // Assuming a thumbnail image exists
    previewUrl: '/videos/Nature_Fox.mp4',
    downloadUrl: '/videos/Nature_Fox.mp4',
    provider: 'local',
  },
  {
    id: 'Bird_Flying',
    title: 'Bird Flying',
    description: 'A bird flying in the sky.',
    thumbnail: '/videos/Bird_Flying.jpg',
    previewUrl: '/videos/Bird_Flying.mp4',
    downloadUrl: '/videos/Bird_Flying.mp4',
    provider: 'local',
  },
];

export const fetchFromLocal = async (): Promise<VideoResource[]> => {
  return Promise.resolve(localVideos);
};
