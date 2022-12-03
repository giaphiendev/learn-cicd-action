ass_weight = 0.2
mid_weight = 0.3
fin_weight = 0.5


def weight_average(list_nums, list_weights):
    weight_sum = 0
    res = 0
    for i in range(len(list_nums)):
        res += list_nums[i] * list_weights[i]
        weight_sum += list_weights[i]

    return round(res / weight_sum, 1)


def cal_avg_grade(obj_grade):
    grade_values = []
    grade_weights = []

    if obj_grade.get('ASSIGNMENT'):
        grade_values.append(obj_grade.get('ASSIGNMENT'))
        grade_weights.append(ass_weight)

    if obj_grade.get('MIDDLE'):
        grade_values.append(obj_grade.get('MIDDLE'))
        grade_weights.append(mid_weight)

    if obj_grade.get('FINAL'):
        grade_values.append(obj_grade.get('FINAL'))
        grade_weights.append(fin_weight)
    if len(grade_values) == 0: return
    return weight_average(grade_values, grade_weights)


def cal_gpa(list_obj_grade):
    res = 0
    for item in list_obj_grade:
        res += item.get('AVG')
    return round(res / len(list_obj_grade), 1)
