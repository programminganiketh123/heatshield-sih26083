"""Curated State -> District -> City/Town coordinate dataset for India.

This is a prototype/demo dataset (a representative sample of districts per
state and union territory), not an exhaustive list of all ~780 Indian
districts. Extend the lists below to add full coverage.

Structure:
    INDIA_LOCATIONS = {
        "State name": {
            "District name": [("City/Town name", lat, lon), ...],
            ...
        },
        ...
    }
"""

INDIA_LOCATIONS = {
    "Andhra Pradesh": {
        "Visakhapatnam": [("Visakhapatnam", 17.6868, 83.2185)],
        "Krishna": [("Vijayawada", 16.5062, 80.6480)],
        "Guntur": [("Guntur", 16.3067, 80.4365)],
        "Tirupati": [("Tirupati", 13.6288, 79.4192)],
        "Kurnool": [("Kurnool", 15.8281, 78.0373)],
    },
    "Arunachal Pradesh": {
        "Papum Pare": [("Itanagar", 27.0844, 93.6053)],
        "Tawang": [("Tawang", 27.5859, 91.8594)],
        "East Siang": [("Pasighat", 28.0667, 95.3260)],
        "Lower Subansiri": [("Ziro", 27.5486, 93.8320)],
    },
    "Assam": {
        "Kamrup Metropolitan": [("Guwahati", 26.1445, 91.7362)],
        "Dibrugarh": [("Dibrugarh", 27.4728, 94.9120)],
        "Cachar": [("Silchar", 24.8333, 92.7789)],
        "Jorhat": [("Jorhat", 26.7509, 94.2037)],
        "Sonitpur": [("Tezpur", 26.6528, 92.7926)],
    },
    "Bihar": {
        "Patna": [("Patna", 25.5941, 85.1376)],
        "Gaya": [("Gaya", 24.7955, 84.9994)],
        "Bhagalpur": [("Bhagalpur", 25.2425, 86.9842)],
        "Muzaffarpur": [("Muzaffarpur", 26.1225, 85.3906)],
        "Darbhanga": [("Darbhanga", 26.1542, 85.8918)],
    },
    "Chhattisgarh": {
        "Raipur": [("Raipur", 21.2514, 81.6296)],
        "Bilaspur": [("Bilaspur", 22.0797, 82.1409)],
        "Durg": [("Durg", 21.1904, 81.2849)],
        "Korba": [("Korba", 22.3595, 82.7501)],
        "Bastar": [("Jagdalpur", 19.0748, 82.0281)],
    },
    "Goa": {
        "North Goa": [("Panaji", 15.4909, 73.8278)],
        "South Goa": [("Margao", 15.2832, 73.9862)],
    },
    "Gujarat": {
        "Ahmedabad": [("Ahmedabad", 23.0225, 72.5714)],
        "Surat": [("Surat", 21.1702, 72.8311)],
        "Vadodara": [("Vadodara", 22.3072, 73.1812)],
        "Rajkot": [("Rajkot", 22.3039, 70.8022)],
        "Bhavnagar": [("Bhavnagar", 21.7645, 72.1519)],
    },
    "Haryana": {
        "Gurugram": [("Gurugram", 28.4595, 77.0266)],
        "Faridabad": [("Faridabad", 28.4089, 77.3178)],
        "Panipat": [("Panipat", 29.3909, 76.9635)],
        "Hisar": [("Hisar", 29.1492, 75.7217)],
        "Karnal": [("Karnal", 29.6857, 76.9905)],
    },
    "Himachal Pradesh": {
        "Shimla": [("Shimla", 31.1048, 77.1734)],
        "Kullu": [("Kullu", 31.9578, 77.1095), ("Manali", 32.2432, 77.1892)],
        "Kangra": [("Dharamshala", 32.2190, 76.3234)],
        "Solan": [("Solan", 30.9045, 77.0967)],
        "Mandi": [("Mandi", 31.7084, 76.9319)],
    },
    "Jharkhand": {
        "Ranchi": [("Ranchi", 23.3441, 85.3096)],
        "East Singhbhum": [("Jamshedpur", 22.8046, 86.2029)],
        "Dhanbad": [("Dhanbad", 23.7957, 86.4304)],
        "Bokaro": [("Bokaro", 23.6693, 86.1511)],
        "Hazaribagh": [("Hazaribagh", 23.9925, 85.3616)],
    },
    "Karnataka": {
        "Bengaluru Urban": [("Bengaluru", 12.9716, 77.5946)],
        "Mysuru": [("Mysuru", 12.2958, 76.6394)],
        "Dakshina Kannada": [("Mangaluru", 12.9141, 74.8560)],
        "Dharwad": [("Hubballi", 15.3647, 75.1240)],
        "Belagavi": [("Belagavi", 15.8497, 74.4977)],
    },
    "Kerala": {
        "Thiruvananthapuram": [("Thiruvananthapuram", 8.5241, 76.9366)],
        "Ernakulam": [("Kochi", 9.9312, 76.2673)],
        "Kozhikode": [("Kozhikode", 11.2588, 75.7804)],
        "Thrissur": [("Thrissur", 10.5276, 76.2144)],
        "Kollam": [("Kollam", 8.8932, 76.6141)],
    },
    "Madhya Pradesh": {
        "Bhopal": [("Bhopal", 23.2599, 77.4126)],
        "Indore": [("Indore", 22.7196, 75.8577)],
        "Jabalpur": [("Jabalpur", 23.1815, 79.9864)],
        "Gwalior": [("Gwalior", 26.2183, 78.1828)],
        "Ujjain": [("Ujjain", 23.1765, 75.7885)],
    },
    "Maharashtra": {
        "Mumbai City": [("Mumbai", 19.0760, 72.8777)],
        "Pune": [("Pune", 18.5204, 73.8567)],
        "Nagpur": [("Nagpur", 21.1458, 79.0882)],
        "Nashik": [("Nashik", 19.9975, 73.7898)],
        "Chhatrapati Sambhajinagar": [("Chhatrapati Sambhajinagar", 19.8762, 75.3433)],
    },
    "Manipur": {
        "Imphal West": [("Imphal", 24.8170, 93.9368)],
    },
    "Meghalaya": {
        "East Khasi Hills": [("Shillong", 25.5788, 91.8933)],
    },
    "Mizoram": {
        "Aizawl": [("Aizawl", 23.7271, 92.7176)],
    },
    "Nagaland": {
        "Kohima": [("Kohima", 25.6751, 94.1086)],
        "Dimapur": [("Dimapur", 25.9091, 93.7278)],
    },
    "Odisha": {
        "Khordha": [("Bhubaneswar", 20.2961, 85.8245)],
        "Cuttack": [("Cuttack", 20.4625, 85.8828)],
        "Sundargarh": [("Rourkela", 22.2604, 84.8536)],
        "Puri": [("Puri", 19.8135, 85.8312)],
        "Sambalpur": [("Sambalpur", 21.4669, 83.9756)],
    },
    "Punjab": {
        "Amritsar": [("Amritsar", 31.6340, 74.8723)],
        "Ludhiana": [("Ludhiana", 30.9010, 75.8573)],
        "Jalandhar": [("Jalandhar", 31.3260, 75.5762)],
        "Patiala": [("Patiala", 30.3398, 76.3869)],
        "Bathinda": [("Bathinda", 30.2110, 74.9455)],
    },
    "Rajasthan": {
        "Jaipur": [("Jaipur", 26.9124, 75.7873)],
        "Jodhpur": [("Jodhpur", 26.2389, 73.0243)],
        "Udaipur": [("Udaipur", 24.5854, 73.7125)],
        "Kota": [("Kota", 25.2138, 75.8648)],
        "Bikaner": [("Bikaner", 28.0229, 73.3119)],
    },
    "Sikkim": {
        "East Sikkim": [("Gangtok", 27.3389, 88.6065)],
    },
    "Tamil Nadu": {
        "Chennai": [("Chennai", 13.0827, 80.2707)],
        "Coimbatore": [("Coimbatore", 11.0168, 76.9558)],
        "Madurai": [("Madurai", 9.9252, 78.1198)],
        "Tiruchirappalli": [("Tiruchirappalli", 10.7905, 78.7047)],
        "Salem": [("Salem", 11.6643, 78.1460)],
    },
    "Telangana": {
        "Hyderabad": [
            ("Hyderabad", 17.3850, 78.4867),
            ("Secunderabad", 17.4399, 78.4983),
            ("Gachibowli", 17.4401, 78.3489),
        ],
        "Warangal": [("Warangal", 17.9689, 79.5941)],
        "Nizamabad": [("Nizamabad", 18.6725, 78.0941)],
        "Karimnagar": [("Karimnagar", 18.4386, 79.1288)],
        "Khammam": [("Khammam", 17.2473, 80.1514)],
    },
    "Tripura": {
        "West Tripura": [("Agartala", 23.8315, 91.2868)],
    },
    "Uttar Pradesh": {
        "Lucknow": [("Lucknow", 26.8467, 80.9462)],
        "Kanpur Nagar": [("Kanpur", 26.4499, 80.3319)],
        "Varanasi": [("Varanasi", 25.3176, 82.9739)],
        "Agra": [("Agra", 27.1767, 78.0081)],
        "Prayagraj": [("Prayagraj", 25.4358, 81.8463)],
        "Gautam Buddh Nagar": [("Noida", 28.5355, 77.3910)],
        "Ghaziabad": [("Ghaziabad", 28.6692, 77.4538)],
    },
    "Uttarakhand": {
        "Dehradun": [("Dehradun", 30.3165, 78.0322), ("Rishikesh", 30.0869, 78.2676)],
        "Haridwar": [("Haridwar", 29.9457, 78.1642)],
        "Nainital": [("Nainital", 29.3919, 79.4542)],
    },
    "West Bengal": {
        "Kolkata": [("Kolkata", 22.5726, 88.3639)],
        "Howrah": [("Howrah", 22.5958, 88.2636)],
        "Darjeeling": [("Siliguri", 26.7271, 88.3953)],
        "Paschim Bardhaman": [("Durgapur", 23.5204, 87.3119), ("Asansol", 23.6739, 86.9524)],
    },
    "Delhi": {
        "New Delhi": [("New Delhi", 28.6139, 77.2090)],
        "North Delhi": [("North Delhi", 28.7041, 77.1025)],
        "South Delhi": [("South Delhi", 28.5245, 77.1855)],
    },
    "Jammu and Kashmir": {
        "Srinagar": [("Srinagar", 34.0837, 74.7973)],
        "Jammu": [("Jammu", 32.7266, 74.8570)],
        "Anantnag": [("Anantnag", 33.7311, 75.1487)],
        "Baramulla": [("Baramulla", 34.2090, 74.3436)],
    },
    "Ladakh": {
        "Leh": [("Leh", 34.1526, 77.5771)],
        "Kargil": [("Kargil", 34.5539, 76.1349)],
    },
    "Puducherry": {
        "Puducherry": [("Puducherry", 11.9416, 79.8083)],
    },
    "Chandigarh": {
        "Chandigarh": [("Chandigarh", 30.7333, 76.7794)],
    },
    "Andaman and Nicobar Islands": {
        "South Andaman": [("Port Blair", 11.6234, 92.7265)],
    },
    "Dadra and Nagar Haveli and Daman and Diu": {
        "Daman": [("Daman", 20.3974, 72.8328)],
        "Dadra and Nagar Haveli": [("Silvassa", 20.2738, 73.0169)],
    },
    "Lakshadweep": {
        "Lakshadweep": [("Kavaratti", 10.5593, 72.6358)],
    },
}
