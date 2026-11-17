import os
import win32com.client
src = os.path.join(os.getcwd(), "Embodied_AI_Visuo_Tactile_Paper_Expanded_v4.docx")
pdf = os.path.join(os.getcwd(), "_v4_preview.pdf")
word = win32com.client.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
doc = word.Documents.Open(src)
print("pages", doc.ComputeStatistics(2))
n = doc.OMaths.Count
print("OMaths", n)
bad = 0
for i in range(1, n+1):
    om = doc.OMaths(i)
    try:
        om.Linearize()
        om.BuildUp()
    except Exception as e:
        bad += 1
        print("bad", i, e)
print("bad", bad)
# print linear forms briefly
for i in range(1, n+1):
    t = doc.OMaths(i).Range.Text.replace("\r", " | ")
    print("%02d" % i, t[:180])
doc.Save()
doc.ExportAsFixedFormat(pdf, 17)
doc.Close(False)
word.Quit()
