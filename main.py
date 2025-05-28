import obs_controller
import bot_interface

if __name__ == "__main__":
    # change_scene("TestBRB")
    obs_controller.download_video("https://www.youtube.com/watch?v=Bjt7mDVCLtk", "testFile1")
    obs_controller.download_video("https://www.youtube.com/watch?v=JP7zsdorPLI", "testFile2")
    obs_controller.download_video("https://www.youtube.com/watch?v=TUzvD4XjBBo", "testFile3")
    obs_controller.download_video("https://www.youtube.com/watch?v=8Bm3le9s3-A", "testFile4")
    pause = input("Waiting...")
    obs_controller.next_set()
    pause = input("Waiting...")
    obs_controller.next_set()
    pause = input("Waiting...")
    obs_controller.next_set()