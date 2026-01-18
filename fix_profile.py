import re

with open(r'c:\Users\Deep Kumar Sinha\OneDrive\Desktop\LocalConnect\templates\vendor\base.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix header shop image - only show emojis or valid base64 images
content = re.sub(
    r'<div class="profile-avatar"[^>]*id="headerShopImage"[^>]*>.*?</div>',
    '''<div class="profile-avatar" id="headerShopImage" onclick="event.stopPropagation(); showShopImageModal();" style="cursor: pointer;" title="Click to change profile image">
                                    {% if vendor_profile and vendor_profile.shop_image %}
                                        {% if vendor_profile.shop_image.startswith('data:image') %}
                                            <img src="{{ vendor_profile.shop_image }}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" onerror="this.innerHTML='🏪';">
                                        {% elif vendor_profile.shop_image|length < 5 %}
                                            {{ vendor_profile.shop_image }}
                                        {% else %}
                                            🏪
                                        {% endif %}
                                    {% else %}
                                        🏪
                                    {% endif %}
                                </div>''',
    content,
    flags=re.DOTALL
)

# Fix dropdown shop image
content = re.sub(
    r'<div class="profile-avatar large"[^>]*id="dropdownShopImage"[^>]*>.*?</div>',
    '''<div class="profile-avatar large" id="dropdownShopImage" onclick="showShopImageModal()" style="cursor: pointer;" title="Click to change image">
                                        {% if vendor_profile and vendor_profile.shop_image %}
                                            {% if vendor_profile.shop_image.startswith('data:image') %}
                                                <img src="{{ vendor_profile.shop_image }}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" onerror="this.innerHTML='🏪';">
                                            {% elif vendor_profile.shop_image|length < 5 %}
                                                {{ vendor_profile.shop_image }}
                                            {% else %}
                                                🏪
                                            {% endif %}
                                        {% else %}
                                            🏪
                                        {% endif %}
                                    </div>''',
    content,
    flags=re.DOTALL
)

with open(r'c:\Users\Deep Kumar Sinha\OneDrive\Desktop\LocalConnect\templates\vendor\base.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed profile images in base.html")