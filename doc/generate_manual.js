const {
  Document, Packer, Paragraph, TextRun, ImageRun, HeadingLevel,
  AlignmentType, PageBreak, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType, TableOfContents,
  Header, Footer, convertInchesToTwip,
  SimpleField
} = require("docx");
const fs = require("fs");
const path = require("path");

const SCREENSHOTS = path.join(__dirname, "screenshots");

function img(filename, w, h) {
  const p = path.join(SCREENSHOTS, filename);
  if (!fs.existsSync(p)) return null;
  return new ImageRun({
    data: fs.readFileSync(p),
    transformation: { width: w || 500, height: h || 300 },
    type: "png",
  });
}

function imgPara(filename, w, h) {
  const i = img(filename, w, h);
  if (!i) return null;
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 120 },
    children: [i],
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 400, after: 120 },
    children: [new TextRun({ text, font: "TH Sarabun New", size: 40, bold: true, color: "1e3a5f" })],
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 280, after: 80 },
    children: [new TextRun({ text, font: "TH Sarabun New", size: 34, bold: true, color: "2563EB" })],
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { before: 200, after: 60 },
    children: [new TextRun({ text, font: "TH Sarabun New", size: 30, bold: true, color: "374151" })],
  });
}

function body(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, font: "TH Sarabun New", size: 28 })],
  });
}

function bold(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({ text, font: "TH Sarabun New", size: 28, bold: true })],
  });
}

function note(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    indent: { left: 360 },
    children: [
      new TextRun({ text: "หมายเหตุ: ", font: "TH Sarabun New", size: 26, bold: true, color: "D97706" }),
      new TextRun({ text, font: "TH Sarabun New", size: 26, color: "D97706" }),
    ],
  });
}

function tip(text) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    indent: { left: 360 },
    children: [
      new TextRun({ text: "เคล็ดลับ: ", font: "TH Sarabun New", size: 26, bold: true, color: "059669" }),
      new TextRun({ text, font: "TH Sarabun New", size: 26, color: "059669" }),
    ],
  });
}

function numbered(items) {
  return items.map((text, i) =>
    new Paragraph({
      spacing: { before: 40, after: 40 },
      indent: { left: 360 },
      children: [
        new TextRun({ text: `${i + 1}. `, font: "TH Sarabun New", size: 28, bold: true }),
        new TextRun({ text, font: "TH Sarabun New", size: 28 }),
      ],
    })
  );
}

function bulleted(items) {
  return items.map((text) =>
    new Paragraph({
      spacing: { before: 40, after: 40 },
      indent: { left: 360 },
      children: [
        new TextRun({ text: "• ", font: "TH Sarabun New", size: 28, bold: true }),
        new TextRun({ text, font: "TH Sarabun New", size: 28 }),
      ],
    })
  );
}

function captionPara(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 40, after: 160 },
    children: [new TextRun({ text, font: "TH Sarabun New", size: 22, italics: true, color: "6B7280" })],
  });
}

function divider() {
  return new Paragraph({
    spacing: { before: 160, after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: "E5E7EB" } },
    children: [],
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function infoBox(title, items) {
  const rows = [
    new TableRow({
      children: [
        new TableCell({
          shading: { type: ShadingType.SOLID, fill: "EFF6FF" },
          margins: { top: 80, bottom: 80, left: 160, right: 160 },
          columnSpan: 2,
          children: [new Paragraph({
            children: [new TextRun({ text: title, font: "TH Sarabun New", size: 28, bold: true, color: "1D4ED8" })]
          })],
        }),
      ],
    }),
    ...items.map(([k, v]) => new TableRow({
      children: [
        new TableCell({
          shading: { type: ShadingType.SOLID, fill: "F9FAFB" },
          margins: { top: 60, bottom: 60, left: 160, right: 80 },
          width: { size: 30, type: WidthType.PERCENTAGE },
          children: [new Paragraph({ children: [new TextRun({ text: k, font: "TH Sarabun New", size: 26, bold: true })] })],
        }),
        new TableCell({
          margins: { top: 60, bottom: 60, left: 80, right: 160 },
          children: [new Paragraph({ children: [new TextRun({ text: v, font: "TH Sarabun New", size: 26 })] })],
        }),
      ],
    })),
  ];
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    margins: { top: 120, bottom: 120 },
    rows,
  });
}

// ===== BUILD DOCUMENT =====

const coverPage = [
  new Paragraph({ spacing: { before: 1200, after: 200 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "ระบบจัดการหน้า Login WiFi ห้องสมุด", font: "TH Sarabun New", size: 56, bold: true, color: "1e3a5f" })],
  }),
  new Paragraph({ spacing: { before: 0, after: 120 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "LibLogin Management System", font: "TH Sarabun New", size: 40, color: "2563EB" })],
  }),
  new Paragraph({ spacing: { before: 120, after: 800 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "─────────────────────────────", font: "TH Sarabun New", size: 28, color: "93C5FD" })],
  }),
  new Paragraph({ spacing: { before: 0, after: 80 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "คู่มือการใช้งานสำหรับเจ้าหน้าที่ห้องสมุด", font: "TH Sarabun New", size: 48, bold: true, color: "374151" })],
  }),
  new Paragraph({ spacing: { before: 80, after: 80 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "User Manual", font: "TH Sarabun New", size: 32, color: "6B7280" })],
  }),
  new Paragraph({ spacing: { before: 800, after: 80 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "สำนักวิทยบริการ มหาวิทยาลัยนครพนม", font: "TH Sarabun New", size: 30, color: "374151" })],
  }),
  new Paragraph({ spacing: { before: 40, after: 40 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "เวอร์ชัน 1.0  |  เมษายน 2568", font: "TH Sarabun New", size: 26, color: "9CA3AF" })],
  }),
  pageBreak(),
];

const tocSection = [
  new Paragraph({ spacing: { before: 200, after: 200 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "สารบัญ", font: "TH Sarabun New", size: 40, bold: true, color: "1e3a5f" })],
  }),
  new TableOfContents("สารบัญ", { hyperlink: true, headingStyleRange: "1-2" }),
  pageBreak(),
];

// ===== CHAPTER 1: บทนำ =====
const ch1 = [
  h1("บทที่ 1: บทนำ"),
  h2("1.1 ภาพรวมระบบ"),
  body("ระบบ LibLogin เป็นระบบจัดการหน้าเข้าสู่เครือข่าย WiFi (Hotspot Login Page) สำหรับห้องสมุด มหาวิทยาลัยนครพนม พัฒนาเพื่อให้เจ้าหน้าที่ห้องสมุดสามารถปรับแต่งหน้าจอ Login ของ WiFi แต่ละจุดได้อย่างสะดวก โดยไม่ต้องแก้ไข code"),
  body("ระบบรองรับการจัดการเนื้อหาหลายรูปแบบ ทั้งรูปพื้นหลัง (Background Image) การตั้งค่า Template หน้า Login รวมถึงเนื้อหา Slide และ Card สำหรับแสดงข้อมูลประชาสัมพันธ์"),
  imgPara("09_hotspot_login.png", 480, 300),
  captionPara("ภาพที่ 1.1 ตัวอย่างหน้า Login WiFi ที่แสดงต่อผู้ใช้งานเครือข่าย"),

  h2("1.2 ความสามารถหลักของระบบ"),
  ...bulleted([
    "จัดการรูปพื้นหลังหน้า Login ได้หลายภาพ แยกตาม Hotspot",
    "กำหนด Template และรูปแบบการแสดงผล (Slideshow / Full Background / Card Gallery)",
    "เพิ่มเนื้อหาประชาสัมพันธ์ผ่าน Slide และ Card",
    "กำหนด URL ปลายทางหลัง Login สำเร็จ (Landing Page)",
    "ดูสถิติการใช้งานและรายงานการเข้าถึง",
  ]),

  h2("1.3 สิ่งที่ต้องการก่อนใช้งาน"),
  infoBox("ข้อกำหนดการใช้งาน", [
    ["Browser", "Google Chrome, Firefox, Edge (เวอร์ชันล่าสุด)"],
    ["URL ระบบ", "https://lib.npu.ac.th/liblogin/"],
    ["การเชื่อมต่อ", "อินเทอร์เน็ต หรือเครือข่ายภายในมหาวิทยาลัย"],
    ["บัญชีผู้ใช้", "ได้รับจากผู้ดูแลระบบ (Admin)"],
  ]),

  h2("1.4 บทบาทผู้ใช้งาน"),
  body("ระบบแบ่งผู้ใช้งานออกเป็น 2 ระดับ:"),
  ...bulleted([
    "เจ้าหน้าที่ทั่วไป (Regular User) — จัดการเนื้อหาได้เฉพาะ Hotspot ที่ได้รับมอบหมายจากหน่วยงาน",
    "ผู้ดูแลระบบ (Admin/Staff) — เข้าถึงได้ทุกส่วน รวมถึงการจัดการผู้ใช้ Hotspot และการตั้งค่าระบบ",
  ]),
  note("คู่มือนี้จัดทำสำหรับ เจ้าหน้าที่ทั่วไป หากต้องการข้อมูลสำหรับผู้ดูแลระบบ กรุณาติดต่อทีม IT"),
  pageBreak(),
];

// ===== CHAPTER 2: การเข้าสู่ระบบ =====
const ch2 = [
  h1("บทที่ 2: การเข้าสู่ระบบและออกจากระบบ"),
  h2("2.1 การเข้าสู่ระบบ"),
  body("เปิด Browser แล้วไปที่ URL: https://lib.npu.ac.th/liblogin/login/"),
  imgPara("01_login.png", 500, 320),
  captionPara("ภาพที่ 2.1 หน้าเข้าสู่ระบบ LibLogin"),
  body("กรอกข้อมูลเพื่อเข้าสู่ระบบ:"),
  ...numbered([
    "กรอก Username ในช่อง \"Username\"",
    "กรอก Password ในช่อง \"Password\"",
    "คลิกปุ่ม \"เข้าสู่ระบบ\"",
  ]),
  imgPara("01_login_filled.png", 500, 320),
  captionPara("ภาพที่ 2.2 กรอก Username และ Password แล้วคลิกเข้าสู่ระบบ"),
  note("หาก Username หรือ Password ไม่ถูกต้อง ระบบจะแสดงข้อความแจ้งเตือน ให้ตรวจสอบข้อมูลและลองใหม่อีกครั้ง"),

  h2("2.2 การออกจากระบบ"),
  body("เมื่อต้องการออกจากระบบ ให้คลิกเมนู \"Logout\" ที่แถบด้านซ้ายล่าง (ส่วน ACCOUNT) ระบบจะนำกลับไปยังหน้า Login"),
  tip("ควรออกจากระบบทุกครั้งหลังเลิกใช้งาน โดยเฉพาะเมื่อใช้คอมพิวเตอร์สาธารณะ"),
  pageBreak(),
];

// ===== CHAPTER 3: Dashboard =====
const ch3 = [
  h1("บทที่ 3: หน้า Dashboard"),
  body("หลังเข้าสู่ระบบสำเร็จ ระบบจะแสดงหน้า Dashboard ซึ่งเป็นหน้าหลักแสดงภาพรวมของระบบ"),
  imgPara("02_dashboard.png", 520, 360),
  captionPara("ภาพที่ 3.1 หน้า Dashboard แสดงสถิติและข้อมูลสรุป"),

  h2("3.1 ข้อมูลสรุปสถิติ (Summary Cards)"),
  body("ส่วนบนของหน้าแสดงตัวเลขสรุปสำคัญ 4 รายการ:"),
  ...bulleted([
    "Background ทั้งหมด — จำนวน Background Image ทั้งหมดในระบบ",
    "กำลังใช้งาน — จำนวน Background ที่มีสถานะ Active อยู่",
    "Hotspot / Router — จำนวน Hotspot ที่กำหนดไว้ในระบบ",
    "ผู้ใช้งานระบบ — จำนวนบัญชีผู้ใช้งาน",
  ]),

  h2("3.2 Background Images ล่าสุด"),
  body("แสดงรายการ Background Image ที่อัปโหลดล่าสุด 5 รายการ พร้อม Preview ขนาดเล็ก ชื่อภาพ Hotspot ที่ใช้งาน สถานะ และวันที่อัปโหลด"),

  h2("3.3 Quick Actions"),
  body("ปุ่มลัดสำหรับงานที่ใช้บ่อย ได้แก่:"),
  ...bulleted([
    "อัปโหลด Background — ไปยังหน้าจัดการรูปพื้นหลัง",
    "จัดการ Templates — ไปยังหน้าจัดการ Template",
    "จัดการหน่วยงาน — ไปยังหน้าจัดการ Department",
    "System Settings — ไปยังหน้าตั้งค่าระบบ (เฉพาะ Admin)",
  ]),

  h2("3.4 การนำทางผ่าน Sidebar"),
  body("แถบด้านซ้ายมือเป็น Sidebar สำหรับนำทางไปยังส่วนต่างๆ ประกอบด้วย:"),
  infoBox("เมนูใน Sidebar", [
    ["CONTENT", "Background Images, Templates, Slide Content, Card Content"],
    ["MANAGEMENT", "Departments, Landing Pages, Monitoring"],
    ["ADMIN", "Hotspots, Users, Settings (เฉพาะ Admin)"],
    ["ACCOUNT", "Logout"],
  ]),
  pageBreak(),
];

// ===== CHAPTER 4: Backgrounds =====
const ch4 = [
  h1("บทที่ 4: จัดการรูปพื้นหลัง (Background Images)"),
  body("หน้า Background Images ใช้สำหรับอัปโหลดและจัดการรูปภาพที่จะแสดงเป็นพื้นหลังบนหน้า Login WiFi คลิกเมนู \"Background Images\" ในแถบ Sidebar"),
  imgPara("03_backgrounds.png", 520, 380),
  captionPara("ภาพที่ 4.1 หน้าจัดการ Background Images"),

  h2("4.1 อัปโหลดรูปพื้นหลังใหม่"),
  body("ส่วนบนของหน้าเป็นฟอร์มอัปโหลดรูปภาพ:"),
  ...numbered([
    "กรอกชื่อภาพในช่อง \"ชื่อภาพ\" (จำเป็นต้องกรอก)",
    "เลือก Hotspot ที่ต้องการใช้ภาพนี้ (ไม่บังคับ — หากไม่เลือกจะใช้กับทุก Hotspot)",
    "เปิด/ปิด Toggle \"ตั้งเป็น Active ทันที\" หากต้องการให้ภาพนี้ใช้งานทันที",
    "คลิกที่กล่องอัปโหลด หรือลากไฟล์ภาพมาวาง",
    "คลิกปุ่ม \"อัปโหลด\"",
  ]),
  note("ระบบรองรับไฟล์ PNG, JPG, JPEG และจะปรับขนาดภาพให้เหลือสูงสุด 1920×1080 พิกเซลโดยอัตโนมัติ"),

  h2("4.2 ดูรายการรูปพื้นหลัง"),
  body("ส่วนล่างแสดงรายการรูปภาพทั้งหมดในรูปแบบ Grid พร้อมข้อมูล:"),
  ...bulleted([
    "Preview รูปภาพขนาดเล็ก (คลิก \"ดูขนาดเต็ม\" เพื่อดูภาพขนาดเต็ม)",
    "ชื่อภาพและ Hotspot ที่ผูกไว้",
    "วันที่อัปโหลด",
    "สถานะ: Active (กำลังใช้งาน) / Inactive (ไม่ได้ใช้งาน)",
  ]),
  tip("ใช้ช่องค้นหาและตัวกรองสถานะด้านบนรายการ เพื่อค้นหาภาพได้รวดเร็วขึ้น"),

  h2("4.3 กำหนดรูปที่ใช้งาน (Set Active)"),
  body("แต่ละ Hotspot สามารถมี Background ที่ Active ได้เพียง 1 ภาพ ขั้นตอนการเปลี่ยน Background:"),
  ...numbered([
    "หารูปภาพที่ต้องการในรายการ",
    "คลิกปุ่ม \"Set Active\" สีน้ำเงิน",
    "ระบบจะเปลี่ยนสถานะรูปนั้นเป็น Active และยกเลิก Active ของรูปเดิมโดยอัตโนมัติ",
  ]),
  note("รูปที่มีสถานะ Active จะไม่มีปุ่ม \"Set Active\" — แสดงเฉพาะแถบ \"Active\" สีเขียว"),

  h2("4.4 แก้ไขข้อมูลรูปภาพ"),
  body("คลิกปุ่ม \"แก้ไข\" เพื่อเปิดหน้าต่างแก้ไขข้อมูล:"),
  imgPara("03b_backgrounds_edit_modal.png", 520, 380),
  captionPara("ภาพที่ 4.2 หน้าต่างแก้ไขข้อมูล Background Image"),
  ...numbered([
    "แก้ไขชื่อภาพหรือ Hotspot ตามต้องการ",
    "สามารถเปลี่ยนรูปภาพใหม่ได้โดยอัปโหลดไฟล์ใหม่",
    "คลิกปุ่ม \"บันทึก\" เพื่อยืนยันการเปลี่ยนแปลง",
  ]),

  h2("4.5 ลบรูปภาพ"),
  body("คลิกปุ่มไอคอนถังขยะ (สีแดง) ด้านขวาของรายการ ระบบจะขอยืนยันก่อนลบ"),
  note("รูปที่มีสถานะ Active ไม่ควรลบ เพราะจะทำให้หน้า Login ไม่มีพื้นหลังแสดง"),
  pageBreak(),
];

// ===== CHAPTER 5: Templates =====
const ch5 = [
  h1("บทที่ 5: จัดการ Template หน้า Login"),
  body("Template กำหนดรูปแบบการแสดงผลบนหน้า Login ว่าจะแสดงเนื้อหาในรูปแบบใด คลิกเมนู \"Templates\" ใน Sidebar"),
  imgPara("04_templates.png", 520, 380),
  captionPara("ภาพที่ 5.1 หน้าจัดการ Template"),

  h2("5.1 ประเภทของ Template"),
  body("ระบบรองรับ Template 3 ประเภท:"),
  infoBox("ประเภท Template", [
    ["Slideshow", "แสดง Slide Content แบบสไลด์โชว์ด้านซ้าย ใช้ร่วมกับ Slide ที่สร้างไว้"],
    ["Full Background", "แสดงพื้นหลังเต็มหน้าจอ ไม่มีเนื้อหาเพิ่มเติม (เรียบง่าย)"],
    ["Card Gallery", "แสดง Card Content แบบ Grid ด้านซ้าย ใช้ร่วมกับ Card ที่สร้างไว้"],
  ]),

  h2("5.2 เพิ่ม Template ใหม่"),
  ...numbered([
    "คลิกปุ่ม \"เพิ่ม Template\" สีน้ำเงิน",
    "กรอกชื่อ Template",
    "เลือกประเภท Component (Slideshow / Full Background / Card Gallery)",
    "เลือก Hotspot ที่ต้องการ (ไม่บังคับ)",
    "คลิก \"บันทึก\"",
  ]),
  imgPara("04b_templates_add_modal.png", 480, 340),
  captionPara("ภาพที่ 5.2 หน้าต่างเพิ่ม Template ใหม่"),

  h2("5.3 แก้ไขและเปิดใช้งาน Template"),
  body("คลิกปุ่ม \"แก้ไข\" เพื่อแก้ไขข้อมูล Template"),
  imgPara("04c_templates_edit_modal.png", 480, 340),
  captionPara("ภาพที่ 5.3 หน้าต่างแก้ไข Template"),
  body("การเปิดใช้งาน Template:"),
  ...bulleted([
    "แต่ละ Hotspot มี Template Active ได้เพียง 1 รายการ",
    "Template ที่ Active จะแสดงแถบ \"ACTIVE\" สีเขียวที่มุมบนซ้าย",
    "คลิกปุ่ม \"Preview\" เพื่อดูตัวอย่างหน้า Login ก่อน Active จริง",
  ]),
  note("หากเลือก Slideshow หรือ Card Gallery ต้องสร้าง Slide / Card ไว้ก่อน มิฉะนั้นหน้า Login จะแสดงเนื้อหาว่างเปล่า"),
  pageBreak(),
];

// ===== CHAPTER 6: Slides =====
const ch6 = [
  h1("บทที่ 6: จัดการ Slide Content"),
  body("Slide Content คือเนื้อหาที่จะแสดงในรูปแบบสไลด์โชว์บนหน้า Login (เมื่อใช้ Template แบบ Slideshow) คลิกเมนู \"Slide Content\" ใน Sidebar"),
  imgPara("05_slides.png", 520, 380),
  captionPara("ภาพที่ 6.1 หน้าจัดการ Slide Content"),

  h2("6.1 ดูรายการ Slide"),
  body("หน้านี้แสดงรายการ Slide ทั้งหมดในรูปแบบตาราง ประกอบด้วย:"),
  ...bulleted([
    "ไอคอน (Emoji หรือรูปภาพ)",
    "หัวข้อและคำอธิบาย",
    "Hotspot ที่ผูกไว้",
    "ลำดับการแสดง (Order) — ตัวเลขน้อยแสดงก่อน",
    "สถานะ Active / Inactive",
  ]),

  h2("6.2 เพิ่ม Slide ใหม่"),
  ...numbered([
    "คลิกปุ่ม \"เพิ่ม Slide ใหม่\"",
    "เลือกประเภทไอคอน: Emoji หรืออัปโหลดรูปภาพ",
    "กรอกหัวข้อ (Title)",
    "กรอกคำอธิบาย (Description)",
    "เลือก Hotspot (ไม่บังคับ)",
    "กำหนดลำดับ (Order) — ตัวเลขน้อยแสดงก่อน",
    "ตั้งค่าการแสดงผล: เปิด/ปิด Title, Description",
    "หากต้องการปุ่ม CTA: เปิด \"Show Link\" แล้วกรอก URL และข้อความปุ่ม",
    "คลิก \"บันทึก\"",
  ]),
  imgPara("05b_slides_add_modal.png", 480, 380),
  captionPara("ภาพที่ 6.2 หน้าต่างเพิ่ม Slide ใหม่"),

  h2("6.3 แก้ไขและลบ Slide"),
  ...bulleted([
    "คลิกปุ่มไอคอนดินสอ (แก้ไข) เพื่อแก้ไขข้อมูล Slide",
    "คลิกปุ่มไอคอนถังขยะ (ลบ) เพื่อลบ Slide ระบบจะขอยืนยันก่อนลบ",
  ]),
  tip("ใช้ฟิลด์ Order เพื่อจัดลำดับ Slide เช่น Slide สำคัญที่สุดให้ใส่ Order = 1"),
  pageBreak(),
];

// ===== CHAPTER 7: Cards =====
const ch7 = [
  h1("บทที่ 7: จัดการ Card Content"),
  body("Card Content คือเนื้อหาที่จะแสดงในรูปแบบการ์ด Grid บนหน้า Login (เมื่อใช้ Template แบบ Card Gallery) คลิกเมนู \"Card Content\" ใน Sidebar"),
  imgPara("06_cards.png", 520, 340),
  captionPara("ภาพที่ 7.1 หน้าจัดการ Card Content"),

  h2("7.1 เพิ่ม Card ใหม่"),
  ...numbered([
    "คลิกปุ่ม \"เพิ่ม Card ใหม่\"",
    "เลือกประเภทไอคอน: Emoji หรืออัปโหลดรูปภาพ",
    "กรอกหัวข้อ (Title)",
    "กรอกคำอธิบาย (Description)",
    "เลือก Hotspot (ไม่บังคับ)",
    "กำหนดลำดับ (Order)",
    "คลิก \"บันทึก\"",
  ]),
  imgPara("06b_cards_add_modal.png", 480, 340),
  captionPara("ภาพที่ 7.2 หน้าต่างเพิ่ม Card ใหม่"),

  h2("7.2 แก้ไขและลบ Card"),
  ...bulleted([
    "คลิกปุ่มไอคอนดินสอ (แก้ไข) เพื่อแก้ไขข้อมูล Card",
    "คลิกปุ่มไอคอนถังขยะ (ลบ) เพื่อลบ Card",
  ]),
  note("Card จะแสดงผลเฉพาะเมื่อ Template ที่ Active เป็นประเภท Card Gallery เท่านั้น"),
  pageBreak(),
];

// ===== CHAPTER 8: Landing Pages =====
const ch8 = [
  h1("บทที่ 8: จัดการ Landing Page"),
  body("Landing Page คือ URL ที่ระบบจะพาผู้ใช้ไปหลังจาก Login WiFi สำเร็จ เช่น เว็บไซต์ห้องสมุด หรือหน้าบริการออนไลน์ คลิกเมนู \"Landing Pages\" ใน Sidebar"),
  imgPara("07_landing_pages.png", 520, 340),
  captionPara("ภาพที่ 8.1 หน้าจัดการ Landing Pages"),

  h2("8.1 เพิ่ม Landing URL ใหม่"),
  ...numbered([
    "คลิกปุ่ม \"Add Landing URL\"",
    "กรอกชื่อ (Title) เช่น \"เว็บไซต์ห้องสมุด\"",
    "กรอก URL ปลายทาง เช่น https://arc.npu.ac.th/",
    "เลือก Hotspot ที่ต้องการ",
    "กำหนด Priority (ตัวเลขน้อย = ความสำคัญสูง)",
    "คลิก \"บันทึก\"",
  ]),
  imgPara("07b_landing_add_modal.png", 480, 340),
  captionPara("ภาพที่ 8.2 หน้าต่างเพิ่ม Landing URL ใหม่"),

  h2("8.2 ดูสถิติ Redirect"),
  body("คอลัมน์ \"REDIRECTS\" แสดงจำนวนครั้งที่ผู้ใช้ถูกพาไปยัง URL นั้น ใช้ประเมินความนิยมของหน้าที่กำหนด"),
  note("แต่ละ Hotspot มี Landing URL Active ได้เพียง 1 รายการ หากต้องการเปลี่ยน ให้แก้ไข URL ของรายการที่ Active อยู่"),
  pageBreak(),
];

// ===== CHAPTER 9: Monitoring =====
const ch9 = [
  h1("บทที่ 9: ดูสถิติการใช้งาน (Monitoring)"),
  body("หน้า Monitoring แสดงสถิติการเข้าชมหน้า Login WiFi ของแต่ละ Hotspot คลิกเมนู \"Monitoring\" ใน Sidebar"),
  imgPara("08_monitoring.png", 520, 380),
  captionPara("ภาพที่ 9.1 หน้า Monitoring แสดงสถิติการใช้งาน"),

  h2("9.1 ข้อมูลสถิติที่แสดง"),
  ...bulleted([
    "จำนวนการเข้าชมทั้งหมด (Total Impressions) แยกตาม Hotspot",
    "จำนวนอุปกรณ์ที่ไม่ซ้ำกัน (Unique Devices)",
    "สัดส่วนอุปกรณ์: มือถือ / คอมพิวเตอร์ / แท็บเล็ต",
    "กราฟแสดงการเข้าชมรายชั่วโมง",
  ]),

  h2("9.2 รายงานการเข้าถึงสื่อ (Media Reach Report)"),
  body("ระบบสามารถสร้างรายงานวิเคราะห์เชิงลึกได้:"),
  ...numbered([
    "เลือก Hotspot และช่วงวันที่ที่ต้องการ",
    "คลิกปุ่ม \"Generate Report\" เพื่อดูรายงานบนหน้าจอ",
    "คลิกปุ่ม \"Export PDF\" เพื่อดาวน์โหลดรายงานเป็นไฟล์ PDF",
  ]),
  body("รายงานประกอบด้วย:"),
  ...bulleted([
    "Reach % — อัตราส่วนผู้ชมที่ไม่ซ้ำกันต่อจำนวนผู้ใช้ทั้งหมด",
    "Frequency — จำนวนครั้งที่ผู้ชมคนหนึ่งเข้าชมโดยเฉลี่ย",
    "Engagement Rate — อัตราการมีส่วนร่วม",
    "การแนะนำช่วงเวลาสื่อสาร (Peak Hours)",
  ]),
  pageBreak(),
];

// ===== CHAPTER 10: FAQ =====
const ch10 = [
  h1("บทที่ 10: คำถามที่พบบ่อย (FAQ)"),

  h2("Q: ลืม Password ทำอย่างไร?"),
  body("ติดต่อผู้ดูแลระบบ (Admin) เพื่อขอรีเซ็ต Password ไม่สามารถรีเซ็ตได้ด้วยตนเองจากหน้า Login"),

  h2("Q: ทำไมอัปโหลดรูปแล้วหน้า Login ยังไม่เปลี่ยน?"),
  ...bulleted([
    "ตรวจสอบว่ารูปมีสถานะ Active หรือไม่ — หากยังเป็น Inactive ให้คลิก \"Set Active\"",
    "ตรวจสอบว่ารูปผูกกับ Hotspot ที่ถูกต้อง หรือเลือกเป็น All Hotspots",
    "รอประมาณ 1-2 นาทีแล้วลอง Refresh หน้า Login อีกครั้ง",
  ]),

  h2("Q: Slide ที่สร้างไว้ไม่แสดงบนหน้า Login?"),
  ...bulleted([
    "ตรวจสอบว่า Template ที่ Active เป็นประเภท Slideshow",
    "ตรวจสอบว่า Slide มีสถานะ Active",
    "ตรวจสอบว่า Slide ผูกกับ Hotspot ที่ถูกต้อง",
  ]),

  h2("Q: เข้าสู่ระบบแล้วเห็นเนื้อหาไม่ครบ?"),
  body("บัญชีของท่านอาจถูกกำหนดให้เห็นเฉพาะเนื้อหาของ Hotspot ในหน่วยงานตนเอง ติดต่อ Admin เพื่อขยายสิทธิ์หากจำเป็น"),

  h2("Q: ต้องการเพิ่ม Hotspot ใหม่ทำอย่างไร?"),
  body("การเพิ่ม Hotspot ต้องทำโดย Admin ผ่านเมนู \"Hotspots\" ซึ่งต้องมีสิทธิ์ Staff เท่านั้น กรุณาติดต่อทีม IT"),

  h2("Q: ติดต่อผู้ดูแลระบบได้ที่ไหน?"),
  infoBox("ข้อมูลติดต่อ", [
    ["หน่วยงาน", "ฝ่ายเทคโนโลยีสารสนเทศ สำนักวิทยบริการ มนพ."],
    ["อีเมล", "arc@npu.ac.th"],
    ["URL ระบบ", "https://lib.npu.ac.th/liblogin/"],
  ]),
];

// ===== ASSEMBLE DOCUMENT =====
const children = [
  ...coverPage,
  // TOC — note: docx auto-generates it, Word needs Ctrl+A then F9 to update
  new Paragraph({ spacing: { before: 200, after: 200 }, alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "สารบัญ", font: "TH Sarabun New", size: 40, bold: true, color: "1e3a5f" })],
  }),
  new TableOfContents("สารบัญ", { hyperlink: true, headingStyleRange: "1-2" }),
  pageBreak(),
  ...ch1, ...ch2, ...ch3, ...ch4, ...ch5, ...ch6, ...ch7, ...ch8, ...ch9, ...ch10,
].filter(Boolean);

const doc = new Document({
  features: { updateFields: true },
  styles: {
    default: {
      document: {
        run: { font: "TH Sarabun New", size: 28 },
        paragraph: { spacing: { line: 360 } },
      },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        run: { font: "TH Sarabun New", size: 40, bold: true, color: "1e3a5f" },
        paragraph: { spacing: { before: 400, after: 120 } },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        run: { font: "TH Sarabun New", size: 34, bold: true, color: "2563EB" },
        paragraph: { spacing: { before: 280, after: 80 } },
      },
      {
        id: "Heading3",
        name: "Heading 3",
        basedOn: "Normal",
        next: "Normal",
        run: { font: "TH Sarabun New", size: 30, bold: true, color: "374151" },
        paragraph: { spacing: { before: 200, after: 60 } },
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: convertInchesToTwip(8.27), height: convertInchesToTwip(11.69) },
          margin: { top: convertInchesToTwip(1), right: convertInchesToTwip(1), bottom: convertInchesToTwip(1), left: convertInchesToTwip(1.25) },
        },
      },
      headers: {
        default: new Header({
          children: [new Paragraph({
            alignment: AlignmentType.RIGHT,
            border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: "E5E7EB" } },
            children: [new TextRun({ text: "คู่มือการใช้งาน LibLogin — สำนักวิทยบริการ มนพ.", font: "TH Sarabun New", size: 20, color: "9CA3AF" })],
          })],
        }),
      },
      footers: {
        default: new Footer({
          children: [new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ text: "หน้า ", font: "TH Sarabun New", size: 22, color: "9CA3AF" }),
              new SimpleField("PAGE"),
            ],
          })],
        }),
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "LibLogin_UserManual.docx");
  fs.writeFileSync(out, buf);
  console.log("✅ สร้างไฟล์สำเร็จ:", out);
}).catch(console.error);
