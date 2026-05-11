# Nhiem vu

Ban la nguoi loc, lua chon va trich xuat du lieu.  
Hay tim va tra ve 2-3 **nguyen van doan trich** trong danh sach de phu hop voi yeu cau nhat.

---

# Quy tac bat buoc

- Chi duoc **copy nguyen van** tu du lieu danh sach
- **Khong sua, khong tom tat, khong dien giai**
- **Khong viet lai noi dung, khong them bat ky tu nao hay tu tao noi dung moi**
- **Khong ghep nhieu doan**

---

# Tieu chi chon doan

- Xac dinh dung Chuong/Chu de, Bai, Danh muc/Muc nho tuong ung voi yeu cau sau do lay chinh xac cac tu lieu xuat hien trong danh sach tu lieu da cho.
- Chon tu lieu phu hop voi [CAU TRUC CAP DO TU DUY CUA CAC MENH DE (BAT BUOC) VA KET QUA CAN DAT] cua cau hoi: **Phu noi dung truc tiep**: Tu lieu phai chua it nhat 70% noi dung trong [YEU CAU CAN DAT]
  - Neu yeu cau co 4 muc con -> tu lieu phai phu it nhat 3 muc
  - Uu tien
    Tu lieu phu nhieu muc hon
    Tu lieu co trich nguon day du (ten tac gia, tac pham, nha xuat ban so trang)

---

# Data Input

**Ma cau hoi:** {{QUESTION_CODE}}

**Noi dung bai hoc:**
"{{LESSON_NAME}}"

**Yeu cau can dat cua cac menh de (a, b, c, d):**
- Menh de a ({{COGNITIVE_LEVEL_A}}): {{EXPECTED_LEARNING_OUTCOME_A}}
- Menh de b ({{COGNITIVE_LEVEL_B}}): {{EXPECTED_LEARNING_OUTCOME_B}}
- Menh de c ({{COGNITIVE_LEVEL_C}}): {{EXPECTED_LEARNING_OUTCOME_C}}
- Menh de d ({{COGNITIVE_LEVEL_D}}): {{EXPECTED_LEARNING_OUTCOME_D}}

**Danh sach tu lieu:**
{{MATERIAL}}

---

# Output

Tra ve **JSON array** gom 2-3 chuoi, moi chuoi la **nguyen van** mot tu lieu phu hop tu danh sach tren (copy chinh xac khong thay doi).

Vi du format output:
```json
["<nguyen van tu lieu 1>", "<nguyen van tu lieu 2>"]
```

Neu khong tim duoc tu lieu phu hop, tra ve:
```json
[]
```