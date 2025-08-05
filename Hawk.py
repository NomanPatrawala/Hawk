import tkinter as tk
from tkinter import ttk, filedialog
import json
import os
from PIL import Image, ImageTk

# --- Post Model ---
class Post:
    def __init__(self, username, content, image_path=None, likes=0, comments=0, retweets=0):
        self.username = username
        self.content = content
        self.image_path = image_path
        self.likes = likes
        self.comments = comments
        self.retweets = retweets

    def to_dict(self):
        return {
            "username": self.username,
            "content": self.content,
            "image_path": self.image_path,
            "likes": self.likes,
            "comments": self.comments,
            "retweets": self.retweets
        }

    @staticmethod
    def from_dict(data):
        return Post(
            data["username"],
            data["content"],
            data.get("image_path"),
            data.get("likes", 0),
            data.get("comments", 0),
            data.get("retweets", 0)
        )

# --- ViewModel ---
class FeedViewModel:
    def __init__(self):
        self.posts = []
        self.load_posts()

    def add_post(self, post):
        self.posts.insert(0, post)
        self.save_posts()

    def delete_post(self, index):
        if 0 <= index < len(self.posts):
            del self.posts[index]
            self.save_posts()

    def like_post(self, index):
        self.posts[index].likes += 1
        self.save_posts()

    def retweet_post(self, index):
        self.posts[index].retweets += 1
        self.save_posts()

    def comment_post(self, index):
        self.posts[index].comments += 1
        self.save_posts()

    def save_posts(self):
        with open("posts.json", "w") as f:
            json.dump([p.to_dict() for p in self.posts], f)

    def load_posts(self):
        if os.path.exists("posts.json"):
            with open("posts.json", "r") as f:
                data = json.load(f)
                self.posts = [Post.from_dict(p) for p in data]

    def search_posts(self, query):
        query = query.lower()
        return [p for p in self.posts if query in p.content.lower() or query in p.username.lower()]

# --- View ---
class FeedView(tk.Frame):
    def __init__(self, master, view_model, top_frame=None):
        super().__init__(master, bg="#e1f5fe")
        self.view_model = view_model
        self.filtered_posts = view_model.posts

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.apply_search())

        if top_frame:
            # Compose UI
            tk.Label(top_frame, text="🧑 Type Your tweet:", bg="#e1f5fe", font=("Segoe UI", 10, "bold")).pack()
            compose_frame = tk.Frame(top_frame, bg="#e1f5fe")
            compose_frame.pack(pady=5)

            self.username_entry = tk.Entry(compose_frame, width=15)
            self.username_entry.insert(0, "@you")
            self.username_entry.pack(side="left", padx=5)

            tk.Label(top_frame, text="📝 What’s happening?", bg="#e1f5fe", font=("Segoe UI", 10, "bold")).pack()
            self.content_entry = tk.Entry(compose_frame, width=40)
            self.content_entry.pack(side="left", padx=5)

            self.image_path = None
            tk.Button(compose_frame, text="📷", command=self.load_image).pack(side="left", padx=5)
            tk.Button(compose_frame, text="Tweet", command=self.add_post).pack(side="left", padx=5)

            search_entry = tk.Entry(top_frame, textvariable=self.search_var, width=50)
            search_entry.pack(pady=5)

        # Scrollable Feed
        self.canvas = tk.Canvas(self, bg="#e1f5fe", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#e1f5fe")

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.render_posts()

    def apply_search(self):
        query = self.search_var.get()
        self.filtered_posts = self.view_model.search_posts(query)
        self.render_posts()

    def load_image(self):
        path = filedialog.askopenfilename(title="Select Image", filetypes=[("Image files", "*.jpg *.png")])
        if path:
            self.image_path = path

    def add_post(self):
        username = self.username_entry.get()
        content = self.content_entry.get()
        post = Post(username, content, self.image_path)
        self.view_model.add_post(post)
        self.image_path = None
        self.search_var.set("")
        self.render_posts()

    def delete_post(self, index):
        actual_index = self.view_model.posts.index(self.filtered_posts[index])
        self.view_model.delete_post(actual_index)
        self.filtered_posts = self.view_model.posts
        self.render_posts()

    def render_posts(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        for idx, post in enumerate(self.filtered_posts):
            frame = tk.Frame(self.scrollable_frame, bg="#ffffff", bd=2, relief="groove", padx=10, pady=5)

            tk.Label(frame, text=post.username, font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#1da1f2").pack(anchor="w")
            tk.Label(frame, text=post.content, font=("Segoe UI", 10), bg="#ffffff",
                     fg="#333333", wraplength=420, justify="left").pack(anchor="w", pady=2)

            if post.image_path and os.path.exists(post.image_path):
                try:
                    img = Image.open(post.image_path)
                    img.thumbnail((400, 300))
                    photo = ImageTk.PhotoImage(img)
                    img_label = tk.Label(frame, image=photo, bg="#ffffff")
                    img_label.image = photo
                    img_label.pack(pady=5)
                except Exception as e:
                    print(f"Image load error: {e}")

            btn_frame = tk.Frame(frame, bg="#ffffff")
            tk.Button(btn_frame, text=f"❤️ {post.likes}", command=lambda i=idx: self.like_post(i),
                      bg="#ffebee", fg="#c62828", relief="flat").pack(side="left", padx=5)
            tk.Button(btn_frame, text=f"💬 {post.comments}", command=lambda i=idx: self.comment_post(i),
                      bg="#e3f2fd", fg="#1565c0", relief="flat").pack(side="left", padx=5)
            tk.Button(btn_frame, text=f"🔁 {post.retweets}", command=lambda i=idx: self.retweet_post(i),
                      bg="#f3e5f5", fg="#6a1b9a", relief="flat").pack(side="left", padx=5)
            tk.Button(btn_frame, text="🗑 Delete", command=lambda i=idx: self.delete_post(i),
                      bg="#ffe0b2", fg="#ef6c00", relief="flat").pack(side="left", padx=5)
            btn_frame.pack(pady=5)

            frame.pack(fill="x", pady=5, padx=10)

    def like_post(self, index):
        actual_index = self.view_model.posts.index(self.filtered_posts[index])
        self.view_model.like_post(actual_index)
        self.render_posts()

    def comment_post(self, index):
        actual_index = self.view_model.posts.index(self.filtered_posts[index])
        self.view_model.comment_post(actual_index)
        self.render_posts()

    def retweet_post(self, index):
        actual_index = self.view_model.posts.index(self.filtered_posts[index])
        self.view_model.retweet_post(actual_index)
        self.render_posts()

# --- Main ---
def main():
    root = tk.Tk()
    root.title("🐦 Twitter Clone (Python)")
    root.geometry("800x700")
    root.configure(bg="#e1f5fe")

    # Top: Compose Section
    top_frame = tk.Frame(root, bg="#e1f5fe")
    top_frame.pack(side="top", fill="x")

    # Bottom: Friends List + Feed
    bottom_frame = tk.Frame(root, bg="#e1f5fe")
    bottom_frame.pack(side="top", fill="both", expand=True)

    # Left: Friends
    left_frame = tk.Frame(bottom_frame, bg="#fce4ec", width=200)
    left_frame.pack(side="left", fill="y")

    tk.Label(left_frame, text="👥 Friends", font=("Segoe UI", 12, "bold"), bg="#fce4ec").pack(pady=10)
    friends = ["@alice", "@bob", "@charlie", "@you", "@elon"]
    for friend in friends:
        tk.Label(left_frame, text=friend, font=("Segoe UI", 10), bg="#fce4ec").pack(anchor="w", padx=10, pady=2)

    # Right: Feed
    right_frame = tk.Frame(bottom_frame, bg="#e1f5fe")
    right_frame.pack(side="right", fill="both", expand=True)

    view_model = FeedViewModel()
    feed_view = FeedView(right_frame, view_model, top_frame=top_frame)
    feed_view.pack(fill="both", expand=True)

    root.mainloop()

if __name__ == "__main__":
    main()
