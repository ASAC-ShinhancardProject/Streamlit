```mermaid
flowchart TB
    A[START\\n사용자 접속] --> B["챗봇 인사\\n\"안녕하세요!\\n매매 목적\\n부동산 상담을 도와드릴까요?\""]

    B --> Q1[Q1. 챗봇:\\n\"현재 어떤 상황이신가요?\\n (1) 신혼부부 여부\\n(2) 부부합산 소득\\n(3) 기존 주택보유 유무\\n등을 알려주세요.\"]

    Q1 --> U1[사용자:\\n\"네, 신혼부부이고\\n부부합산 소득은 O만원,\\n주택은 아직 없어요.\"]

    U1 --> R1[챗봇:\\n\"알겠습니다.\\n조건에 맞는 대출 상품과\\n정책 정보를 정리해드릴게요.\"]

    R1 --> Q2[Q2. 챗봇:\\n\"원하시는 지역 정보를\\n알려주시겠어요?\\n(예: 본가 위치, 직장 위치,\\n중간 지점 등)\"]

    Q2 --> U2[사용자:\\n\"본가는 A(지역),\\n직장은 B(지역)\\n근처로 알아보고 싶어요.\"]

    U2 --> R2[챗봇:\\n\"알겠습니다.\\n해당 지역 인근\\n중간지점 후보들과\\nML 모델 추천 결과를\\n바탕으로 안내해드릴게요.\"]

    R2 --> Q3[Q3. 챗봇(ML 결과 제시):\\n\"아래 단지들이\\n대출조건(소득, 무주택 등)에\\n부합하며, 선호도도 높습니다.\\n1) XX 아파트\\n2) YY 아파트\\n3) ZZ 아파트\\n추가로\\n조정대상지역/투기지역 여부,\\nLTV/DTI, 세금규제도\\n간단히 안내할까요?\"]

    Q3 --> D1{사용자 선택}
    D1 -- "더 알아볼게요" --> Q4[Q4. 사용자:\\n\"예: XX 아파트 가격대,\\n실거래가 추이는?\\n대출 한도 얼마까지\\n가능할까요?\"]

    D1 -- "다른 지역도 알고싶어요" --> Q5[Q5. 사용자:\\n\"C 지역도 궁금합니다.\"]

    D1 -- "상담 종료" --> End[END\\n\"도움 되셨나요?\\n감사합니다!\"]

    Q4 --> R4[챗봇:\\n\"XX 아파트 최근 실거래가\\nOO원대이며, 소득·LTV·규제 고려 시\\n대출 한도 OO만원까지\\n가능할 것으로 보입니다.\"]

    R4 --> Q4_1{추가 질문\\n유/무?}
    Q4_1 -- 예 --> Q4_2[사용자: \"디딤돌 대출이\\n이 상황에 적용되나요?\"]

    Q4_1 -- 아니오 --> D1

    Q4_2 --> R4_2[챗봇: \"디딤돌 대출은\\n연소득 OO 이하,\\n부부합산 O억원 이하 주택,\\n등의 조건이 있습니다.\\n충족 여부 알려드립니다.\"]

    R4_2 --> Q4_1

    Q5 --> R5[챗봇:\\n\"C 지역은 O구역이고\\n규제지역/비규제지역 등\\n특이사항이 있습니다.\\nML 모델 추천 단지:\\n... (간단 리스트)\"]

    R5 --> Q5_1{추가 질문\\n유/무?}
    Q5_1 -- 예 --> Q5_2[사용자:\\n\"C 지역도 실거래가\\n알려주세요.\"]

    Q5_1 -- 아니오 --> D1

    Q5_2 --> R5_2[챗봇:\\n\"C 지역 주요 아파트\\n평균 매매가: OO원,\\n전용 XX㎡ 기준 OO원\\n등...\"]

    R5_2 --> Q5_1

    ...