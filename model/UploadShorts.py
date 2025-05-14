from googleapiclient.http import MediaFileUpload

class YouTubeAPI:

    def upload_video(self, file_path, title, description, category_id, privacy_status='private'):
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'categoryId': category_id,
            },

            'status': {
                'privacyStatus': privacy_status
            }
        }
    
        media = MediaFileUpload(file_path, resumable=True)

        request = self.youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media,
        )

        response = request.execute()
        return response
    

def main():
    print("Hello")

if __name__ == "main":
    main()