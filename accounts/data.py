import pandas as pd
import numpy as np
import random
import string

def random_username(fake=False):
    if fake:
        # fake usernames: random strings with numbers and "bot", "fake"
        prefixes = ['bot', 'fake', 'spam', 'user', 'test']
        return random.choice(prefixes) + ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
    else:
        # real usernames: first+last style or normal names
        first_names = ['john', 'alice', 'mike', 'jane', 'chris', 'mark', 'linda', 'jessica', 'dan', 'kate']
        last_names = ['smith', 'johnson', 'williams', 'jones', 'brown', 'davis', 'miller', 'wilson']
        return random.choice(first_names) + random.choice(last_names) + str(random.randint(1, 99))

def random_bio(fake=False):
    real_bios = [
        "Love hiking and photography.",
        "Tech enthusiast and blogger.",
        "Fitness trainer and nutrition expert.",
        "Travel junkie exploring the world.",
        "Music lover and artist.",
        "Foodie and chef in the making.",
        "Entrepreneur and startup founder.",
        "Bookworm and writer.",
        "Digital marketer and designer.",
        "Student of life and coding."
    ]
    fake_bios = [
        "",  # empty bio common in fake accounts
        "Buy followers here! http://fakefollowers.com",
        "Click here for free gifts!!!",
        "Visit www.scamsite.com for great deals",
        "Get free likes now!",
        "Amazing offers!!! Check this out!!!",
        "Earn $$$ fast and easy!!!",
        "Don't miss this opportunity!!!",
        "Win a free iPhone today!!!",
        "Follow me for more followers!!!"
    ]
    return random.choice(fake_bios) if fake else random.choice(real_bios)

def generate_profile(fake=False):
    username = random_username(fake)
    bio = random_bio(fake)
    if fake:
        followers_count = np.random.randint(0, 200)
        following_count = np.random.randint(500, 3000)
        is_private = np.random.choice([0, 1], p=[0.7, 0.3])
        posts_count = np.random.randint(0, 10)
    else:
        followers_count = np.random.randint(100, 10000)
        following_count = np.random.randint(50, 2000)
        is_private = np.random.choice([0, 1], p=[0.9, 0.1])
        posts_count = np.random.randint(10, 500)
    return {
        'username': username,
        'bio': bio,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_private': is_private,
        'posts_count': posts_count,
        'fake': int(fake)
    }

def generate_dataset(num_samples=10000, fake_ratio=0.3):
    data = []
    num_fake = int(num_samples * fake_ratio)
    num_real = num_samples - num_fake
    
    for _ in range(num_real):
        data.append(generate_profile(fake=False))
    for _ in range(num_fake):
        data.append(generate_profile(fake=True))
    
    # Shuffle the dataset
    random.shuffle(data)
    
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    df = generate_dataset(num_samples=10000, fake_ratio=0.3)
    df.to_csv('training_data.csv', index=False)
    print("✅ training_data.csv generated with 10,000 samples")
