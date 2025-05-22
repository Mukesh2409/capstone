import os
import json
import requests
import http.client
import ssl
import certifi
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Instagram API Configuration
INSTAGRAM_API_KEY = "b5dbfc233cmshfce7bbac76a3571p1a4f92jsn10a6d24d5f1b"
INSTAGRAM_API_HOST = "instagram-scraper-ai1.p.rapidapi.com"

# Ollama Configuration
OLLAMA_API_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama2"  # or "mistral" for faster results

def index(request):
    """Render the main page."""
    return render(request, 'index.html')

def download_image(url, filename):
    """Download and save profile image."""
    try:
        response = requests.get(url, stream=True, verify=certifi.where())
        if response.status_code == 200:
            filepath = os.path.join('wholedata', filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return f'/wholedata/{filename}'
    except Exception as e:
        print(f"Error downloading image: {e}")
    return '/static/default_placeholder.jpg'

def analyze_with_ollama(profile_data):
    """Enhanced profile analysis with sensitive detection."""
    system_prompt = """
    You are an expert Instagram profile authenticity analyst. Examine these aspects critically:
    1. Username patterns (numbers, special chars, mimicry of famous accounts)
    2. Follower/following ratio (0.5-2.0 is normal, <0.1 or >10 is suspicious)
    3. Bio content (ONLY analyze if bio is not 'No bio available')
    4. Verification status (unverified with high followers is suspicious)
    5. Post frequency (0 posts is suspicious, 1-3 posts is new but acceptable)
    6. Profile completeness (missing required info)
    7. Image analysis (generic or stolen profile pictures)

    Score each category 0-100 based on these STRICT rules:
    - Propaganda: Political/controversial content (+30 if detected in ACTUAL content)
    - Extremist: Radical/divisive content (+50 if detected in ACTUAL content)
    - Spam: Follower ratio <0.1 or >10 (+40), 0 posts (+30), generic bio if exists (+20)
    - Hate: Offensive language in ACTUAL bio content only (+60)
    - Incomplete: Missing bio (+20), 0 posts (+20), no profile pic (+30)
    - Impersonating: Clear mimicry of famous account (+50), unverified with >10k followers (+40)

    IMPORTANT:
    - Do NOT analyze non-existent content
    - If bio is 'No bio available', do NOT perform bio analysis
    - Consider 1-3 posts as normal for new accounts
    - Default to 0 score when no suspicious elements found
    """
    system_prompt = """
    You are an expert Instagram profile authenticity analyst. Examine these aspects critically:
    1. Username patterns (numbers, special chars, mimicry of famous accounts)
    2. Follower/following ratio (<0.01 is suspicious, >10 is normal)
    3. Bio content (generic, copied, or suspicious content)
    4. Verification status (unverified with high followers is suspicious)
    5. Post frequency (sudden spikes or no posts)
    6. Profile completeness (missing basic info)
    7. Image analysis (generic or stolen profile pictures)

    Score each category 0-100 based on these rules:
    - Propaganda: Political/controversial content (+30 if detected)
    - Extremist: Radical/divisive content (+50 if detected)
    - Spam: Follower ratio <0.01 (+70), posts < 1 (+30), generic bio (+20)
    - Hate: Offensive language (+60 if detected)
    - Incomplete: Missing bio (+40), posts < 3 (+30), no profile pic (+30)
    - Impersonating: Mimics famous account (+50), unverified with 10k+ followers (+40)

    Return STRICTLY in this JSON format:
    {
        "categories": {
            "propaganda": {"score": 0-100, "reason": "..."},
            "extremist": {"score": 0-100, "reason": "..."},
            "spam": {"score": 0-100, "reason": "..."},
            "hate": {"score": 0-100, "reason": "..."},
            "incomplete": {"score": 0-100, "reason": "..."},
            "impersonating": {"score": 0-100, "reason": "..."}
        },
        "image_analysis": "Normal/Extremist/Spam/Violent/Hate",
        "risk_score": 0-100,
        "conclusion": "Authentic/Suspicious/Fake",
        "detailed_reason": "2-3 sentence explanation"
    }
    Use "-" for reasons when score is 0.
    """

    user_prompt = f"""
    Analyze this Instagram profile:
    Username: {profile_data.get('username', 'N/A')}
    Full Name: {profile_data.get('full_name', 'N/A')}
    Followers: {profile_data.get('follower_count', 0)}
    Following: {profile_data.get('following_count', 0)}
    Posts: {profile_data.get('media_count', 0)}  # This shows 2 posts
    Bio: {profile_data.get('biography', 'No bio available')}
    Verified: {'Yes' if profile_data.get('is_verified') else 'No'}
    Private: {'Yes' if profile_data.get('is_private') else 'No'}
    Profile Pic: {profile_data.get('profile_pic_url', 'No image')}

    Note: Consider actual post count in analysis. Do not mark as "no posts" if post count > 0.
    """

    try:
        response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.7}
            },
            timeout=120
        )
        result = response.json()
        return json.loads(result.get("message", {}).get("content", "{}"))
    except Exception as e:
        print(f"Ollama error: {e}")
        return None

def generate_html_analysis(analysis):
    """Convert analysis JSON to HTML format"""
    if not analysis or not analysis.get("categories"):
        return """
        <div class="analysis-error">
            <p>⚠️ Analysis failed. Please try again.</p>
        </div>
        """
    
    cats = analysis["categories"]
    return f"""
    <div class="final_output">
        <h3>Profile Analysis Results</h3>
        <table>
            <tr>
                <td>Propaganda Content</td>
                <td><span class="score {get_score_class(cats['propaganda']['score'])}">
                    {cats['propaganda']['score']}%
                </span></td>
                <td><span class="reason">{cats['propaganda']['reason'] or '-'}</span></td>
            </tr>
            <tr>
                <td>Extremist Content</td>
                <td><span class="score {get_score_class(cats['extremist']['score'])}">
                    {cats['extremist']['score']}%
                </span></td>
                <td><span class="reason">{cats['extremist']['reason'] or '-'}</span></td>
            </tr>
            <tr>
                <td>Spam Activity</td>
                <td><span class="score {get_score_class(cats['spam']['score'])}">
                    {cats['spam']['score']}%
                </span></td>
                <td><span class="reason">{cats['spam']['reason'] or '-'}</span></td>
            </tr>
            <tr>
                <td>Hate Speech</td>
                <td><span class="score {get_score_class(cats['hate']['score'])}">
                    {cats['hate']['score']}%
                </span></td>
                <td><span class="reason">{cats['hate']['reason'] or '-'}</span></td>
            </tr>
            <tr>
                <td>Incomplete Profile</td>
                <td><span class="score {get_score_class(cats['incomplete']['score'])}">
                    {cats['incomplete']['score']}%
                </span></td>
                <td><span class="reason">{cats['incomplete']['reason'] or '-'}</span></td>
            </tr>
            <tr>
                <td>Impersonation</td>
                <td><span class="score {get_score_class(cats['impersonating']['score'])}">
                    {cats['impersonating']['score']}%
                </span></td>
                <td><span class="reason">{cats['impersonating']['reason'] or '-'}</span></td>
            </tr>
        </table>
        
        <div class="summary">
            <div class="risk-score">
                <span>Overall Risk: </span>
                <span class="risk {get_risk_class(analysis['risk_score'])}">
                    {analysis['risk_score']}%
                </span>
            </div>
            <div class="image-analysis">
                <span>Image Analysis: </span>
                <span class="tag {analysis['image_analysis'].lower()}">
                    {analysis['image_analysis']}
                </span>
            </div>
            <div class="conclusion">
                <p><strong>Conclusion:</strong> {analysis['conclusion']}</p>
                <p class="detailed-reason">{analysis['detailed_reason']}</p>
            </div>
        </div>
    </div>
    """

def get_score_class(score):
    """Get CSS class for score value"""
    if score >= 70: return "high"
    if score >= 40: return "medium"
    return "low"

def get_risk_class(score):
    """Get CSS class for risk score"""
    if score >= 70: return "high-risk"
    if score >= 40: return "medium-risk"
    return "low-risk"

@csrf_exempt
def wholeinsta_fetch(request):
    """Fetch and analyze Instagram profile"""
    if request.method == "POST":
        conn = None
        try:
            # Parse JSON data from request body instead of form data
            data = json.loads(request.body)
            username = data.get("username")
            
            if not username:
                return JsonResponse({"error": "Username required"}, status=400)

            # Fetch from Instagram API
            conn = http.client.HTTPSConnection(
                INSTAGRAM_API_HOST,
                context=ssl.create_default_context(cafile=certifi.where())
            )
            
            headers = {
                'x-rapidapi-key': INSTAGRAM_API_KEY,
                'x-rapidapi-host': INSTAGRAM_API_HOST
            }
            
            endpoint = f"/user/info_v2/?username={username}"
            conn.request("GET", endpoint, headers=headers)
            response = conn.getresponse()
            
            if response.status != 200:
                return JsonResponse(
                    {"error": f"Instagram API error: {response.status}"},
                    status=response.status
                )
            
            data = json.loads(response.read().decode("utf-8"))
            
            if not (isinstance(data, dict) and "data" in data and "user" in data["data"]):
                return JsonResponse({"error": "Invalid profile data"}, status=400)
                
            user_info = data["data"]["user"]
            
            # Prepare profile data
            profile_data = {
                'username': user_info.get('username', ''),
                'full_name': user_info.get('full_name', ''),
                'follower_count': int(user_info.get('follower_count', 0)),
                'following_count': int(user_info.get('following_count', 0)),
                'media_count': int(user_info.get('media_count', 0)),
                'biography': user_info.get('biography', 'No bio available'),
                'is_verified': user_info.get('is_verified', False),
                'is_private': user_info.get('is_private', False),
                'profile_pic_url': download_image(
                    user_info.get('profile_pic_url', ''),
                    f"{user_info.get('username', 'profile')}.jpg"
                )
            }

            # Get AI analysis
            ai_result = analyze_with_ollama(profile_data)
            
            return JsonResponse({
                "success": True,
                "profile": profile_data,
                "analysis": ai_result,
                "analysis_html": generate_html_analysis(ai_result) if ai_result else None
            })
            
        except json.JSONDecodeError as e:
            return JsonResponse({"error": f"Invalid API response: {str(e)}"}, status=500)
        except http.client.HTTPException as e:
            return JsonResponse({"error": f"HTTP error: {str(e)}"}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        finally:
            if conn:
                conn.close()
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def ai_analysis(request):
    """Direct AI analysis endpoint"""
    if request.method == "POST":
        try:
            profile_data = json.loads(request.body)
            ai_result = analyze_with_ollama(profile_data)
            return JsonResponse({
                "success": bool(ai_result),
                "analysis": ai_result,
                "analysis_html": generate_html_analysis(ai_result) if ai_result else None
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Method not allowed"}, status=405)